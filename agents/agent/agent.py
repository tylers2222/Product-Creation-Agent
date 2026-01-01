from typing import Protocol, TypedDict
import json
from pydantic import BaseModel
import structlog

from langgraph.graph import START, StateGraph, END
from qdrant_client.models import PointStruct
from agents.infrastructure.shopify_api.product_schema import DraftProduct, DraftResponse
from .schema import ScraperResponse
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
from .llm import llm_client, LLM
from .prompts import markdown_summariser_prompt
from .tools import create_all_tools
from config import create_service_container, ServiceContainer

logger = structlog.get_logger(__name__)

class AgentProtocol(Protocol):
    """Protocol for abstracting the agent workflow"""
    def service_workflow(self, query: str):
        ...

class AgentState(TypedDict):
    """State of agent operations"""
    request_id: str
    query: str # the original query the user writes
    extract_query: str # the extracted query from hte LLM
    validated_data: dict # dictionary representation of the product and its internal data
    web_scraped_data: ScraperResponse # the result of the web scraping operation
    similar_products: list[PointStruct]
    filled_data: DraftProduct # fill the draft struct with draft data
    shopify_response: DraftResponse
    inventory_filled: bool

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
        logger.debug("Inititalising ShopifyProductWorkflow class")

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
        self.workflow.add_node("inventory_filled", self.inventory)

        self.workflow.add_edge(START, "query_extract")
        self.workflow.add_edge("query_extract", "query_scrape")
        self.workflow.add_edge("query_scrape", "query_synthesis")
        self.workflow.add_edge("query_synthesis", "fill_data")
        self.workflow.add_edge("fill_data", "post_shopify")
        self.workflow.add_edge("post_shopify", "inventory_filled")
        self.workflow.add_edge("inventory_filled", END)

        self.app = self.workflow.compile()
        logger.info("Successfully initialised ShopifyProductWorkflow class")

    def query_extract(self, state: AgentState):
        request_id = state.get("request_id", None)
        logger.debug("Starting query_extract node for request %s", request_id)
        parser = PydanticOutputParser(pydantic_object=QueryResponse)
        format_instructions = parser.get_format_instructions()
        
        prompt = f"""STEP 1: VALIDATE USER INPUT

User Query: {state["query"]}

Your job is to UNDERSTAND what the user is asking for and extract key information.

REQUIRED OUTPUTS:
1. query: The search query to use for finding the product online (usually the product name and brand)
2. extract_query: A refined query focusing on key product identifiers (brand + product name)
3. validated_data: A dictionary with this EXACT structure:
   {{
     "brand_name": "string",
     "product_name": "string",
     "variants": [
       {{
         "option1_value": {{"option_name": "Size", "option_value": "50 g"}},
         "option2_value": {{"option_name": "Flavor", "option_value": "Chocolate"}} OR null,
         "option3_value": null OR {{"option_name": "Type", "option_value": "Premium"}},
         "sku": 12345,
         "barcode": "0810095637971",
         "price": 4.95,
         "compare_at": null OR 9.99,
         "product_weight": 0.05,
         "inventory_at_stores": null OR {{"city": 15, "south_melbourne": 15}}
       }}
     ]
   }}

CRITICAL RULES:
1. option1_value, option2_value, option3_value MUST be objects with "option_name" and "option_value" fields, NOT strings
2. product_weight MUST be in KILOGRAMS (kg). Convert: 50g = 0.05, 2kg = 2.0, 5lb ≈ 2.27
3. Extract ALL variants mentioned - each unique size/flavor combination is a separate variant
4. If a variant has multiple options (size + flavor), include BOTH option1_value AND option2_value
5. barcode should be a string (can have leading zeros)
6. If compare_at price is not mentioned, use null
7. INVENTORY_AT_STORES: Look for inventory numbers in the input. If mentioned, extract as {{"city": <number>, "south_melbourne": <number>}}. Common patterns:
   - "city: 15, south_melbourne: 15"
   - "inventory: 15, 15"
   - "City: 15, South Melbourne: 15"
   - "inventory_at_stores: {{city: 15, south_melbourne: 15}}"
   - If inventory numbers are the same for all variants, apply to all variants
   - If inventory numbers are NOT mentioned anywhere in the input, use null

EXAMPLE 1 (with inventory):
Input: "Create EHP OxyShred Protein Lean Bar, 50g in White Choc Caramel, Strawberries & Cream, Choc Peanut Caramel, Cookies & Cream, all $4.95, inventory: city=15, south_melbourne=15"

Output validated_data:
{{
  "brand_name": "EHP",
  "product_name": "OxyShred Protein Lean Bar",
  "variants": [
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "White Choc Caramel"}}, "sku": 922026, "barcode": "0810095637971", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": {{"city": 15, "south_melbourne": 15}}}},
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Strawberries & Cream"}}, "sku": 922028, "barcode": "0810095637933", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": {{"city": 15, "south_melbourne": 15}}}},
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Choc Peanut Caramel"}}, "sku": 922027, "barcode": "0810095637988", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": {{"city": 15, "south_melbourne": 15}}}},
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Cookies & Cream"}}, "sku": 922029, "barcode": "0810095637945", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": {{"city": 15, "south_melbourne": 15}}}}
  ]
}}

EXAMPLE 2 (without inventory):
Input: "Create EHP OxyShred Protein Lean Bar, 50g in White Choc Caramel, Strawberries & Cream, all $4.95"

Output validated_data:
{{
  "brand_name": "EHP",
  "product_name": "OxyShred Protein Lean Bar",
  "variants": [
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "White Choc Caramel"}}, "sku": 922026, "barcode": "0810095637971", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": null}},
    {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Strawberries & Cream"}}, "sku": 922028, "barcode": "0810095637933", "price": 4.95, "compare_at": null, "product_weight": 0.05, "inventory_at_stores": null}}
  ]
}}

{format_instructions}
"""
        llm_response = self.llm.invoke_mini(system_query = None, user_query=prompt)
        query_response = parser.parse(llm_response)

        logger.debug("query_response: %s", query_response, request_id=request_id)
        logger.info("Completed query_extract", request_id=request_id)
        return {
            "query": query_response.query,
            "extracted_query": query_response.extract_query,
            "validated_data": query_response.validated_data,
        }

    def query_scrape(self, state: AgentState):
        """A simple scrape search node in the pipeline"""
        request_id = state.get("request_id", None)
        logger.debug("Started query_scrape node", request_id=request_id if request_id else "Unknown")
        search_products_and_similar = search_products_comprehensive(query=state["query"], scraper=self.scraper, embeddor=self.embeddor, vector_db=self.vector_db, llm=self.llm)
        
        logger.debug("Similar Products Returned: %s", search_products_and_similar[1])
        logger.info("Completed query_scrape", request_id=request_id if request_id else "Unknown")
        return {
            "web_scraped_data": search_products_and_similar[0],
            "similar_products": search_products_and_similar[1]
        }

    def query_synthesis(self, state: AgentState):
        """A node that evaluates vector DB relevance and summarizes markdown content"""
        request_id = state.get("request_id", None)
        logger.debug("Started query_synthesis node", request_id=request_id if request_id else "Unknown")

        # Step 1: Handle markdown summarization
        web_data = state.get("web_scraped_data", None)
        if web_data is None:
            logger.error("No web data returned", request_id=request_id if request_id else "Unknown")
            raise Exception("No web data returned")
        
        summarisations_needed = web_data.markdowns_needings_summarisation()
        for needed in summarisations_needed:
            result = self.llm.invoke_mini(user_query=markdown_summariser_prompt(title=web_data.query, markdown=needed["markdown"]))
            logger.info(f"Summarized markdown at index {needed['idx']}", request_id=request_id if request_id else "Unknown")
            web_data.result[needed["idx"]] = result
        
        similar_products = state["similar_products"]
        target_info = web_data.query
        logger.debug("Similar Products: %s", similar_products, request_id=request_id if request_id else "Unknown")
        logger.debug("Query Wanting Similar Products For: %s", target_info, request_id=request_id if request_id else "Unknown")
        similar_products_simple = [
            {
                "id": str(p.id),
                "title": p.payload.get("title", "Unknown"),
                "product_type": p.payload.get("product_type", "Unknown")
            }
            for p in similar_products
        ]

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

        logger.debug("Output Text: %s", output_text)

        relevance_result = parser.parse(output_text)
        
        logger.info(f"Vector DB relevance: {relevance_result.relevance_score}% ({relevance_result.matches}/{relevance_result.total})", request_id=request_id if request_id else "Unknown")
        logger.info(f"Action taken: {relevance_result.action_taken}", request_id=request_id if request_id else "Unknown")
        logger.debug(f"Reasoning: {relevance_result.reasoning}", request_id=request_id if request_id else "Unknown")
        
        if relevance_result.action_taken == "requery":
            # Note: The LLM returns simplified dicts, but we need to keep original PointStruct objects
            # For now, just log that a requery happened - the tool should have updated the data
            if not relevance_result.similar_products:
                raise Exception("Agent claimed to requery but returned empty results")

            similar_products = relevance_result.similar_products
            logger.info("Agent performed requery for better similar products", request_id=request_id if request_id else "Unknown")

        logger.info("Complete query_synthesis", request_id=request_id if request_id else "Unknown")
        return {
            "web_scraped_data": web_data,
            "similar_products": similar_products
        }

    def fill_data(self, state: AgentState):
        """A node that builds out the draft product for our shopify store"""
        request_id = state.get("request_id", None)
        logger.debug("Started fill_data node", request_id=request_id if request_id else "Unknown")

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
2. TITLE: Extract complete product name from scraped data -> Vendor Name then product name ALWAYS
3. DESCRIPTION: Synthesize from scraped data in HTML format
4. VENDOR: Extract brand name from scraped data
5. TYPE: Copy the product_type from similar products (they show our store's categories)
6. TAGS: Copy tag style from similar products - match their format (uppercase/lowercase, style)
7. LEAD_OPTION: Set to the option_name from option1_value (usually "Size")
8. BABY_OPTIONS: CRITICAL - If ANY variant has option2_value, you MUST set baby_options to a list containing the option_name from option2_value (e.g., ["Flavor"] or ["Flavour"]). If variants have option3_value, add that option_name too (e.g., ["Flavor", "Type"]). If NO variants have option2_value, set baby_options to null.

CRITICAL RULE FOR BABY_OPTIONS:
- If variants have option2_value → baby_options MUST be ["Flavor"] (or whatever the option_name is)
- If variants have option3_value → baby_options MUST include both option names (e.g., ["Flavor", "Type"])
- If NO variants have option2_value → baby_options MUST be null

EXAMPLE:
If variants are:
[
  {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Chocolate"}}, ...}},
  {{"option1_value": {{"option_name": "Size", "option_value": "50 g"}}, "option2_value": {{"option_name": "Flavor", "option_value": "Vanilla"}}, ...}}
]

Then:
- lead_option: "Size"
- baby_options: ["Flavor"]  ← MUST include this!

EXAMPLE - If similar products have:
- Type: "Protein Powder"
- Tags: ["Protein", "Whey", "Sports Nutrition"]

Then use the SAME style for your product.

{format_instructions}
"""
        fill_data_response_text = self.llm.invoke_max(system_query=None, user_query=prompt)
        fill_data_response = parser.parse(fill_data_response_text)

        logger.debug("Fill Data Response: %s", fill_data_response)
        logger.info("Completed fill_data", request_id=request_id if request_id else "Unknown")
        return {
            "filled_data": fill_data_response
        }

    def post_shopify(self, state: AgentState):
        """A node that posts the response to shopify"""
        request_id = state.get("request_id", None)
        logger.debug("Starting post_shopify node", request_id=request_id if request_id else "Unknown")
        # fix issue with the concrete not being obtained properly
        draft = state.get("filled_data", None)
        if draft is None:
            raise TypeError("Draft returned none from the state")
        shop_response = shop_svc(draft_product=draft, shop=self.shop)

        logger.debug("shop_response: %s", shop_response, request_id=request_id if request_id else "Unknown")
        logger.info("Completed post_shopify")
        return {
            "shopify_response": shop_response
        }

    def inventory(self, state: AgentState):
        request_id = state.get("request_id", None)
        logger.debug("Started inventory node", request_id=request_id if request_id else "Unknown")

        draft_response = state.get("shopify_response")

        inv_item_ids = draft_response.variant_inventory_item_ids

        completed = 0
        failed = 0
        for item in inv_item_ids:
            try:
                completed = self.shop.fill_inventory(inventory_data=item)
                if completed:
                    completed += 1
            except Exception as e:
                logger.error(f"item {item.inventory_item_id} failed to updated inventory", request_id=request_id if request_id else "Unknown")
                failed += 1

        logger.info(f"Completed inventory, Completed {completed}, Failed {failed}", request_id=request_id if request_id else "Unknown")
        if failed > 0:
            return {
                "inventory_filled": False
            }
        
        return {
                "inventory_filled": True
            } 

    async def service_workflow(self, query: str, request_id: str) -> DraftResponse:
        logger.info("Starting service workflow", request_id=request_id if request_id else "Unknown")

        result = self.app.invoke({"query": query, "request_id": request_id})
        return result.get("shopify_response", None)

def create_agent() -> ShopifyProductWorkflow:
    try:
        sc = create_service_container()  # Call the function!
        tools = create_all_tools(sc)

        return ShopifyProductWorkflow(shop=sc.shop, scraper=sc.scraper, vector_db=sc.vector_db, embeddor=sc.embeddor, llm=sc.llm, tools=tools)

    except AttributeError as a:
        logger.error("Service Container: %s", sc.to_json())
        raise AttributeError(a)