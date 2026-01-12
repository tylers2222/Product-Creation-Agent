import logging
from langchain_core.output_parsers import PydanticOutputParser

from models.product_generation import QueryResponse

from agents.agent.prompts import PromptVariant, markdown_summariser_prompt
from agents.infrastructure.firecrawl_api.client import Scraper
from agents.infrastructure.vector_database.embeddings import Embeddor
from agents.infrastructure.vector_database.db import VectorDb
from agents.infrastructure.shopify_api.client import Shop
from agents.agent.llm import LLM

logger = logging.getLogger(__name__)

class ShopifyProductCreateService:
    """A workflow in the service layer that executes nodes"""
    def __init__(self, shop: Shop, scraper: Scraper, vector_db: VectorDb, embeddor: Embeddor, llm: LLM, tools: list):
        self.llm = llm
        self.shop = shop
        self.scraper = scraper
        self.vector_db = vector_db
        self.embeddor = embeddor

        
    def query_extract(self, request_id: str, query: PromptVariant):
        """First node that ensures quality when searching google via the scraper"""
        logger.debug("Starting query_extract node for request %s", request_id)

        query.brand_name = query.brand_name.title()
        query.product_name = query.product_name.title()

        parser = PydanticOutputParser(pydantic_object=QueryResponse)
        format_instructions = parser.get_format_instructions()
        
        prompt = f"""
STEP 1: Synthesise the incoming request for google search

If you think {query.brand_name} {query.product_name}
Is going to produce the best google results, leave it as is {query.brand_name} {query.product_name}, otherwise formulate the best string to search

{format_instructions}
"""
        llm_response = self.llm.invoke_mini(system_query = None, user_query=prompt)
        query_response = parser.parse(llm_response)

        logger.debug("query_response: %s", query_response, request_id=request_id)
        logger.info("Completed query_extract", request_id=request_id)
        return query_response

    def check_if_product_already_exists(query: PromptVariant):
        # Run vector db check & shopify sku check in parralel?
        # Do vector search first potentially
        # Need to get sharper in vector databases here, can you vector search json, do you search small parts of a listing
        
