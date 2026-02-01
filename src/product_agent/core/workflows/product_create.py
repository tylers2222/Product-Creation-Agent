from typing import Protocol, TypedDict
import json
from product_agent.infrastructure.llm.prompts import PromptVariant
import structlog

from langgraph.graph import START, StateGraph, END
from qdrant_client.models import PointStruct
from product_agent.infrastructure.shopify.schemas import DraftProduct, DraftResponse
from langchain_core.output_parsers import PydanticOutputParser
from product_agent.core.agent_configs.synthesis import SYNTHESIS_CONFIG
from product_agent.config import build_service_container, ServiceContainer, build_synthesis_agent

from product_agent.services.agent_workflows.product_creation import ShopifyProductCreateService
from product_agent.services.infrastructure.vector_search import product_similarity_threshold_svc
from product_agent.models.scraper import ScraperResponse

logger = structlog.get_logger(__name__)

class AgentProtocol(Protocol):
    """Protocol for abstracting the agent workflow"""
    def service_workflow(self, query: str):
        ...

class AgentState(TypedDict):
    """State of agent operations"""
    request_id:             str
    query:                  PromptVariant # the original query the user writes
    adapted_search_string:  str # the upgraded google search query
    validated_data:         dict # dictionary representation of the product and its internal data
    web_scraped_data:       ScraperResponse # the result of the web scraping operation
    similar_products:       list[PointStruct]
    filled_data:            DraftProduct # fill the draft struct with draft data
    shopify_response:       DraftResponse
    inventory_filled:       bool

class ShopifyProductWorkflow:
    def __init__(self, container: ServiceContainer):
        """
        Initialize the Shopify product workflow.

        Args:
            container: ServiceContainer with all dependencies
        """
        logger.debug("Inititalising ShopifyProductWorkflow class")

        # Store dependencies from container
        self.shop = container.shop
        self.scraper = container.scraper
        self.vector_db = container.vector_db
        self.embeddor = container.embeddor
        self.llm = container.llm["open_ai"]

        self.product_create_service = ShopifyProductCreateService(sc=container, tools=None)

        self.agent = build_synthesis_agent(container, SYNTHESIS_CONFIG)

        self.workflow = StateGraph(AgentState)
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

    async def query_extract(self, state: AgentState):
        request_id = state.get("request_id", None)
        if request_id is None:
            logger.error("No request id retrieved", state=state)
            raise ValueError("No request id retrieved")
        
        query = state.get("query", None)
        if query is None:
            logger.error("No Query schema recieved", state=state)

        query_response = await self.product_create_service.query_extract(request_id, query)
        return {
            "adapted_search_string": query_response.adapted_search_string,
        }

    def check_if_exists(self, state: AgentState):
        """Check if product already exists in the store."""
        # TODO: Implement product existence check
        # use the services to one line these nodes
        pass

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

        similar_products = state["similar_products"]
        target_info = state["adapted_search_string"]
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

    async def fill_data(self, state: AgentState):
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
- baby_options: ["Flavour"]  ← MUST include this!

EXAMPLE - If similar products have:
- Type: "Protein Powder"
- Tags: ["Protein", "Whey", "Sports Nutrition"]

Then use the SAME style for your product.
"""
        from ..models.llm_input import LLMInput
        llm_input = LLMInput(
            model="max_deterministic",
            system_query=None,
            user_query=prompt,
            response_schema=DraftProduct,
            verbose=False
        )
        fill_data_response_text = await self.llm.invoke(llm_input)

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
    """
    Factory function to create a fully-configured ShopifyProductWorkflow.

    Returns:
        ShopifyProductWorkflow with all dependencies injected
    """
    try:
        container = build_service_container()
        return ShopifyProductWorkflow(container=container)

    except AttributeError as e:
        logger.error("Failed to create agent", error=str(e))
        raise