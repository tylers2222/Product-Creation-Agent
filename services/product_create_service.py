import inspect
import asyncio
import structlog
import json
from langchain_classic.agents import AgentExecutor
from langchain_core.output_parsers import PydanticOutputParser
from qdrant_client.models import PointStruct

from factory import ServiceContainer, agents

from models.product_generate.query_extract import QueryResponse
from models.product_generate.vector_relevance import VectorRelevanceResponse

from agents.agent.prompts import PromptVariant, markdown_summariser_prompt

from services.internal.vector_db import SimilarityResult, product_similarity_threshold_svc
from services.internal.scraper import scrape_results_svc
from services.schema import ProductExists

logger = structlog.getLogger(__name__)

class ShopifyProductCreateService:
    """A workflow in the service layer that executes nodes"""
    def __init__(self, sc: ServiceContainer, synthesis_agent: AgentExecutor):
        self.llm = sc.llm
        self.shop = sc.shop
        self.scraper = sc.scraper
        self.vector_db = sc.vector_db
        self.embeddor = sc.embeddor

        self.synthesis_agent = synthesis_agent
        
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

    def query_scrape(self, query: str):
        """Scraper in the service layer"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        logger.debug("Checking query data", query=query)
        
        scraper_response = scrape_results_svc(search_str=query, 
            scraper=self.scraper, llm=self.llm)
        
        # scraper response has a few fields that can be used to track and see what data is being worked with
        logger.debug("Completed scraper response", scraper_response=scraper_response)
        return scraper_response

    def query_synthesis(self, query: str, similar_products: list[PointStruct]):
        """Agent call for relevance of similar products in service layer"""
        parser = PydanticOutputParser(pydantic_object=VectorRelevanceResponse)
        format_instructions = parser.get_format_instructions()
        
        agent_input = f"""You are analyzing product search results for relevance.

TARGET PRODUCT: {query}

CURRENT SIMILAR PRODUCTS:
{json.dumps(similar_products, default=str)}

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
        
        resp = self.synthesis_agent.invoke({"input": agent_input})
        output_text = resp.get("output", "")

        logger.debug("Output Text: %s", output_text)

        relevance_result = parser.parse(output_text)
        
        logger.info(f"Vector DB relevance: {relevance_result.relevance_score}% ({relevance_result.matches}/{relevance_result.total})",)
        logger.info(f"Action taken: {relevance_result.action_taken}")
        logger.debug(f"Reasoning: {relevance_result.reasoning}")
        
        if relevance_result.action_taken == "requery":
            # Note: The LLM returns simplified dicts, but we need to keep original PointStruct objects
            # For now, just log that a requery happened - the tool should have updated the data
            if not relevance_result.similar_products:
                raise ValueError("Agent claimed to requery but returned empty results")

            similar_products = relevance_result.similar_products
            logger.info("Agent performed requery for better similar products")

        logger.debug("Complete query_synthesis")
