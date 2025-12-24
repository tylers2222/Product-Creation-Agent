from langgraph.graph import START, StateGraph, END
from typing import Protocol, TypedDict
import structlog

from qdrant_client.models import PointStruct
from agents.infrastructure.shopify_api.product_schema import DraftProduct, DraftResponse
from .schema import ScraperResponse
from pydantic import BaseModel
from agents.infrastructure.shopify_api.client import Shop
from agents.infrastructure.firecrawl_api.client import Scraper
from agents.infrastructure.vector_database.db import VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddor, Embeddings
from agents.infrastructure.vector_database.db import vector_database
from agents.infrastructure.firecrawl_api.client import FirecrawlClient
from agents.infrastructure.shopify_api.client import ShopifyClient
from .agent_definitions import synthesis_agent
from .services import search_products_comprehensive, shop_svc
from langchain_core.output_parsers import PydanticOutputParser
from .llm import LLM, llm_client
from .prompts import markdown_summariser_prompt
from .tools import ServiceContainer, create_all_tools
import json

# Configure structlog for scoped logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get the base logger
logger = structlog.get_logger()

class AgentProtocol(Protocol):
    def service_workflow(self, query: str):
        ...

class AgentState(TypedDict):
    query: str # the original query the user writes
    extract_query: str # the extracted query from hte LLM
    validated_data: dict # dictionary representation of the product and its internal data
    web_scraped_data: ScraperResponse # the result of the web scraping operation
    similar_products: list[PointStruct]
    filled_data: DraftProduct # fill the draft struct with draft data
    shopify_response: dict

# Pydantic models for responses
class QueryResponse(BaseModel):
    query: str
    extract_query: str
    validated_data: dict

class QuerySynthesis(BaseModel):
    web_scraped_data: ScraperResponse
    similar_products: list[PointStruct]

class VectorRelevanceResponse(BaseModel):
    relevance_score: int
    matches: int
    total: int
    action_taken: str
    reasoning: str
    similar_products: list[dict]

# Main LLM Client Class
class ShopifyProductWorkflow:
    def __init__(self, shop: Shop, scraper: Scraper, vector_db: VectorDb, embeddor: Embeddor, llm: LLM, tools: list):
        self.llm = llm
        self.workflow = StateGraph(AgentState)
        self.shop = shop
        self.scraper = scraper
        self.vector_db = vector_db
        self.embeddor = embeddor
        self.agent = synthesis_agent(tools=tools)

        self.workflow.add_node("query_extract", self.query_extract)
        self.workflow.add_node("query_scrape", self.query_scrape)
        self.workflow.add_node("query_synthesis", self.query_synthesis)
        self.workflow.add_node("fill_data", self.fill_data)
        self.workflow.add_node("post_shopify", self.post_shopify)

        self.workflow.add_edge(START, "query_extract")
        self.workflow.add_edge("query_extract", "query_scrape")
        self.workflow.add_edge("query_scrape", "query_synthesis")
        self.workflow.add_edge("query_synthesis", "fill_data")
        self.workflow.add_edge("fill_data", "post_shopify")
        self.workflow.add_edge("post_shopify", END)

        logger.info("Successfully completed workflow")
        self.app = self.workflow.compile()

    def query_extract(self, state: AgentState):
        parser = PydanticOutputParser(pydantic_object=QueryResponse)
        format_instructions = parser.get_format_instructions()
        
        prompt = f"""STEP 1: VALIDATE USER INPUT

User Query: {state["query"]}

Your job is to UNDERSTAND what the user is asking for and extract key information.

REQUIRED OUTPUTS:
1. query: The search query to use for finding the product online (usually the product name and brand)
2. extract_query: A refined query focusing on key product identifiers (brand + product name)
3. validated_data: A dictionary containing the variants information

For EACH variant the user mentions, you need to find:
- Size/quantity (5lb, 2kg, 1000g, etc.)
- Flavor/variant type (Chocolate, Vanilla, etc.) - if applicable

Do NOT require a specific format. Use your understanding to extract the information.

{format_instructions}
"""
        llm_response = self.llm.invoke_mini(system_query = None, user_query=prompt)

        query_response = parser.parse(llm_response)

        logger.info("Completed query_extract")

        return {
            "query": query_response.query,
            "extracted_query": query_response.extract_query,
            "validated_data": query_response.validated_data,
        }

    def query_scrape(self, state: AgentState):
        """A simple scrape search node in the pipeline"""
        search_products_and_similar = search_products_comprehensive(query=state["query"], scraper=self.scraper, embeddor=self.embeddor, vector_db=self.vector_db, llm=self.llm)
        
        logger.info("Completed query_scrape")
        return {
            "web_scraped_data": search_products_and_similar[0],
            "similar_products": search_products_and_similar[1]
        }

    def query_synthesis(self, state: AgentState):
        """A node that evaluates vector DB relevance and summarizes markdown content"""
        
        # Step 1: Handle markdown summarization
        web_data = state.get("web_scraped_data", None)
        if web_data is None:
            logger.error("No web data returned")
            raise Exception("No web data returned")
        
        summarisations_needed = web_data.markdowns_needings_summarisation()
        for needed in summarisations_needed:
            result = self.llm.invoke_mini(user_query=markdown_summariser_prompt(title=web_data.query, markdown=needed["markdown"]))
            logger.info(f"Summarized markdown at index {needed['idx']}")
            web_data.result[needed["idx"]] = result
        
        # Step 2: Evaluate vector DB search relevance
        similar_products = state["similar_products"]
        target_info = web_data.query
        similar_products_simple = [
            {
                "id": str(p.id),
                "title": p.payload.get("title", "Unknown"),
                "product_type": p.payload.get("product_type", "Unknown")
            }
            for p in similar_products
        ]

        # Parse the relevance response
        parser = PydanticOutputParser(pydantic_object=VectorRelevanceResponse)
        format_instructions = parser.get_format_instructions()
        
        agent_input = f"""You are analyzing product search results for relevance.

TARGET PRODUCT: {target_info}

CURRENT SIMILAR PRODUCTS:
{json.dumps(similar_products_simple, default=str)}

STEP 1 - CALCULATE RELEVANCE:
Count how many products match the target product's category.
Relevance = (matches / total) × 100

STEP 2 - DECISION:
If relevance < 50%:
  → YOU MUST CALL the get_similar_products tool RIGHT NOW with the product category
  → Wait for the tool to return results
  → Include ALL results from the tool in your final JSON

If relevance >= 50%:
  → Use the current products

STEP 3 - FORMAT OUTPUT:
{format_instructions}

IMPORTANT: If you need to call get_similar_products, DO IT NOW before returning JSON. The similar_products field must contain ACTUAL tool results, not an empty array.
"""
        
        resp = self.agent.invoke({"input": agent_input})
        output_text = resp.get("output", "")

        print(f"\n\nOutput Text: {output_text}")

        relevance_result = parser.parse(output_text)
        
        logger.info(f"Vector DB relevance: {relevance_result.relevance_score}% ({relevance_result.matches}/{relevance_result.total})")
        logger.info(f"Action taken: {relevance_result.action_taken}")
        logger.info(f"Reasoning: {relevance_result.reasoning}")
        
        similar_products = similar_products
        if relevance_result.action_taken == "requery":
            # Note: The LLM returns simplified dicts, but we need to keep original PointStruct objects
            # For now, just log that a requery happened - the tool should have updated the data
            if not relevance_result.similar_products:
                raise Exception("Agent claimed to requery but returned empty results")

            similar_products = relevance_result.similar_products
            logger.info("Agent performed requery for better similar products")

        return {
            "web_scraped_data": web_data,
            "similar_products": similar_products
        }

    def fill_data(self, state: AgentState):
        """A node that builds out the draft product for our shopify store"""

        parser = PydanticOutputParser(pydantic_object=DraftProduct)
        format_instructions = parser.get_format_instructions()

        prompt = f"""CREATE PRODUCT LISTING

USER'S VARIANT SPECIFICATIONS (USE THESE EXACTLY):
{state["validated_data"]}

WEB SCRAPED DATA (for product details):
{state["web_scraped_data"]}

SIMILAR PRODUCTS (for style/formatting reference):
{json.dumps(state["similar_products"], default=str)}

INSTRUCTIONS:
1. VARIANTS: Create exactly the variants specified in validated_data (with their SKUs, barcodes, prices)
2. TITLE: Extract complete product name from scraped data
3. DESCRIPTION: Synthesize from scraped data in HTML format
4. VENDOR: Extract brand name from scraped data
5. TYPE: Copy the product_type from similar products (they show our store's categories)
6. TAGS: Copy tag style from similar products - match their format (uppercase/lowercase, style)

EXAMPLE - If similar products have:
- Type: "Protein Powder"
- Tags: ["Protein", "Whey", "Sports Nutrition"]

Then use the SAME style for your product.

{format_instructions}
"""
        fill_data_response_text = self.llm.invoke_max(system_query=None, user_query=prompt)
        fill_data_response = parser.parse(fill_data_response_text)

        logger.info("Completed fill_data")
        return {
            "filled_data": fill_data_response
        }

    def post_shopify(self, state: AgentState):
        """A node that posts the response to shopify"""
        # fix issue with the concrete not being obtained properly
        draft = state.get("filled_data", None)
        if draft is None:
            raise TypeError("Draft returned none from the state")
        shop_response = shop_svc(draft_product=draft, shop=self.shop)

        logger.info("Completed post_shopify")
        return {
            "shopify_response": shop_response
        }

    async def service_workflow(self, query: str) -> DraftResponse:
        print("Starting Workflow")

        result = self.app.invoke({"query": query})
        return result.get("shopify_response", None)

def create_agent() -> ShopifyProductWorkflow:
    sc = ServiceContainer(
        vector_db=vector_database(),
        embeddor=Embeddings(),
        scraper=FirecrawlClient(),
        shop=ShopifyClient(),
        llm=llm_client()
    )
    tools = create_all_tools(sc)

    return ShopifyProductWorkflow(shop=sc.shop, scraper=sc.scraper, vector_db=sc.vector_db, embeddor=sc.embeddor, llm=sc.llm, tools=tools)