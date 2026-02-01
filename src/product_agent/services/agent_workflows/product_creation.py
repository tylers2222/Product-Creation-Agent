import inspect
import asyncio
import json
import structlog
from langchain_classic.agents import AgentExecutor
from langchain_core.output_parsers import PydanticOutputParser
from qdrant_client.models import PointStruct


from product_agent.config import ServiceContainer, agents

from product_agent.models.query import QueryResponse
from product_agent.models.relevance import VectorRelevanceResponse
from product_agent.models.scraper import ScraperResponse

from product_agent.infrastructure.llm.prompts import PromptVariant, markdown_summariser_prompt
from product_agent.infrastructure.synthesis.agent import Agent
from product_agent.infrastructure.shopify.schemas import DraftProduct, DraftResponse

from product_agent.services.infrastructure.vector_search import SimilarityResult, product_similarity_threshold_svc
from product_agent.services.infrastructure.scraping import scrape_results_svc
from product_agent.services.schemas import ProductExists
from product_agent.models.llm_input import LLMInput

from product_agent.services.orchestrators.product_search import search_products_comprehensive

logger = structlog.getLogger(__name__)

class ShopifyProductCreateService:
    """
    A workflow in the service layer that executes nodes
    
    Unresolved thoughts:
        Multiple LLMs:
            If one runs out of credis, can use another
            Can test outputs and judge

        Retry On Specific Errors for nodes
    """
    def __init__(self, sc: ServiceContainer, synthesis_agent: Agent):
        self.llm = sc.llm["open_ai"]
        self.shop = sc.shop
        self.scraper = sc.scraper
        self.vector_db = sc.vector_db
        self.embeddor = sc.embeddor

        self.synthesis_agent = synthesis_agent
        
    async def query_extract(self, query: PromptVariant) -> QueryResponse:
        """
        First node that ensures quality when searching google via the scraper
        Returns:
            adapted_search_string: A string best for getting product listings from online
            brand_product: The brand name and product name to align with naming conventions
            ∆ this may change due to the fact different companies can have different naming conventions
        """
        logger.debug("Starting %s", inspect.stack()[0][3])

        query.brand_name = query.brand_name.title()
        query.product_name = query.product_name.title()
        brand_product = f"{query.brand_name} {query.product_name}"
        prompt = f"""
STEP 1: Synthesise the incoming request for google search

If you think {brand_product}
Is going to produce the best google results, leave it as is {brand_product}, otherwise formulate the best string to search for shops selling it, so we can scrape them
"""
        llm_input = LLMInput(
            model="mini_deterministic",
            system_query=None,
            user_query=prompt,
            response_schema=QueryResponse,
            verbose=False
        )
        llm_response = await self.llm.invoke(llm_input)
        llm_response.brand_product = brand_product

        logger.debug("query_response: %s", llm_response)
        logger.info("Completed query_extract")
        return llm_response

    async def check_if_product_already_exists(self, query: PromptVariant) -> ProductExists | None:
        """Checking if a product exists node"""
        # Run vector db check & shopify sku check in parralel?
        # Do vector search first potentially
        # Need to get sharper in vector databases here, can you vector search json, do you search small parts of a listing
        # will need to give this function scope to the webhook that will likely be open between the front end and this agent operation
        # TODO: Implement this function
        logger.debug("Starting %s", inspect.stack()[0][3])
        logger.debug("Checking query data", query=query)

        document = f"{query.brand_name} {query.product_name}"
        document_embedded = self.embeddor.embed_document(document=document)

        logger.debug("Document embedded", embed=document_embedded)

        # we will use sku 1 in the variants list for now but need to work out a solution here
        executables_result = await asyncio.gather(
            self.shop.search_by_sku(sku=query.variants[0].sku),
            product_similarity_threshold_svc(vector_query=document_embedded, vector_db=self.vector_db))

        logger.debug("Finished the asyncio gather")
        
        shopify_res = executables_result[0]
        logger.debug("Shopify Result returned", shopify_result=shopify_res)
        if shopify_res is not None:
            logger.debug("Shopify found a matching SKU", shopify_result=shopify_res)
            return ProductExists(
                product_name=shopify_res.product.title,
                sku=shopify_res.sku,
                method="shopify"
            )

        similarity_threshold = executables_result[1]
        logger.debug("Similarity Threshold returned", similarity_threshold=similarity_threshold)
        if similarity_threshold is not None:
            logger.debug("Similarity threshold exceeded", similarity_result=similarity_threshold)
            return ProductExists(
                product_name=similarity_threshold.product_name,
                score=similarity_threshold.score,
                method="vector_search"
            )

        return None

    def query_scrape(self, query: str) -> tuple:
        """Scraper and vector database collection in the service layer"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        logger.debug("Checking query data", query=query)
        
        scraper_and_vector_search = search_products_comprehensive(query=query,
            scraper=self.scraper, embeddor=self.embeddor, vector_db=self.vector_db, llm=self.llm)
        
        # scraper response has a few fields that can be used to track and see what data is being worked with
        logger.debug("Completed scraper response")
        return scraper_and_vector_search

    def query_synthesis(self, query: str, similar_products: list[PointStruct]) -> VectorRelevanceResponse:
        """Agent call for relevance of similar products in service layer"""
        similar_products_simple = [
            {
                "id": str(p.id),
                "title": p.payload.get("title"),
                "product_type": p.payload.get("product_type"),
                "vendor": p.payload.get("vendor"),
                "tags": p.payload.get("tags"),
            }
            for p in similar_products
        ]
        agent_input = f"""You are analyzing product search results for relevance.

TARGET PRODUCT: {query}

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
        
        resp = self.synthesis_agent.invoke(agent_input, VectorRelevanceResponse)
        logger.debug("Returned response from agent", resp=resp)
        if resp.action_taken == "requery":
            # Note: The LLM returns simplified dicts, but we need to keep original PointStruct objects
            # For now, just log that a requery happened - the tool should have updated the data
            if not resp.similar_products:
                raise ValueError("Agent claimed to requery but returned empty results")
            logger.info("Agent performed requery for better similar products")

        logger.debug("Complete query_synthesis")
        return resp


    async def fill_data(self, validated_data: dict, web_scraped_data: ScraperResponse, similar_products: list[PointStruct]):
        logger.debug("Starting %s", inspect.stack()[0][3])

        prompt = f"""CREATE PRODUCT LISTING

USER'S VARIANT SPECIFICATIONS (USE THESE EXACTLY):
{validated_data}

WEB SCRAPED DATA (for product details):
{web_scraped_data}

SIMILAR PRODUCTS (for style/formatting reference):
{json.dumps(similar_products, default=str)}

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

        llm_input = LLMInput(
            model="max_deterministic",
            system_query=None,
            user_query=prompt,
            response_schema=DraftProduct,
            verbose=False
        )
        fill_response = await self.llm.invoke(llm_input)
        logger.debug("LLM completed draft product data", fill_response=fill_response)
        return fill_response

    def inventory(self, shopify_response: DraftResponse):
        """Filling the inventory in the service layer"""
        logger.debug("Starting %s", inspect.stack()[0][3])

        inv_item_ids = shopify_response.variant_inventory_item_ids

        completed = 0
        failed = 0
        for item in inv_item_ids:
            try:
                completed = self.shop.fill_inventory(inventory_data=item)
                if completed:
                    completed += 1
            except Exception as e:
                logger.error("item %s failed to updated inventory", item.inventory_item_id)
                failed += 1

        logger.info("Completed inventory, Completed %s, Failed %s", completed, failed)
        if failed > 0:
            return {
                "inventory_filled": False
            }
        return {
                "inventory_filled": True
            }

