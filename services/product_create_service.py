import inspect
import asyncio
from langchain_core.output_parsers import PydanticOutputParser
import structlog

from config import ServiceContainer

from models.product_generation import QueryResponse

from agents.agent.prompts import PromptVariant, markdown_summariser_prompt
from agents.infrastructure.firecrawl_api.client import Scraper
from agents.infrastructure.vector_database.embeddings import Embeddor
from agents.infrastructure.vector_database.db import VectorDb
from agents.infrastructure.shopify_api.client import Shop
from agents.agent.llm import LLM

from services.internal.vector_db import SimilarityResult, product_similarity_threshold_svc
from services.schema import ProductExists

logger = structlog.getLogger(__name__)

class ShopifyProductCreateService:
    """A workflow in the service layer that executes nodes"""
    def __init__(self, sc: ServiceContainer, tools: list | None):
        self.llm = sc.llm
        self.shop = sc.shop
        self.scraper = sc.scraper
        self.vector_db = sc.vector_db
        self.embeddor = sc.embeddor

        
    def query_extract(self, request_id: str, query: PromptVariant):
        """First node that ensures quality when searching google via the scraper"""
        logger.debug("Starting query_extract node for request %s", request_id)

        query.brand_name = query.brand_name.title()
        query.product_name = query.product_name.title()
        
        prompt = f"""
STEP 1: Synthesise the incoming request for google search

If you think {query.brand_name} {query.product_name}
Is going to produce the best google results, leave it as is {query.brand_name} {query.product_name}, otherwise formulate the best string to search
"""
        llm_response = self.llm.invoke_mini(system_query = None, user_query=prompt, response_schema=QueryResponse)

        logger.debug("query_response: %s", llm_response, request_id=request_id)
        logger.info("Completed query_extract", request_id=request_id)
        return llm_response

    async def check_if_product_already_exists(self, query: PromptVariant) -> ProductExists:
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

    
