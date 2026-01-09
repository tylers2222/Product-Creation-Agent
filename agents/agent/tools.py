from langchain.tools import tool
import structlog
from dataclasses import dataclass

from agents.infrastructure.firecrawl_api.client import FirecrawlClient, FireResult, Scraper
from agents.infrastructure.shopify_api.client import ShopifyClient, DraftProduct, Shop
from agents.infrastructure.vector_database.db import VectorDb, vector_database
from agents.infrastructure.vector_database.embeddings import Embeddings, Embeddor
from config import ServiceContainer
from .services import embed_search_svc, similarity_search_svc

logger = structlog.get_logger(__name__)

def create_all_tools(container: ServiceContainer) -> list:
    logger.debug("Creating all the tools for agent use")
    @tool
    def get_similar_products(query: str):
        """
        A tool used to take what a customer is searching for an search in our own database
        
        Use cases include:
        If you think the similarity results are driven by a brands name instead of the product type, request more
        Method - Cut out the brand name and re attempt a similarity search without it
        """
        query_embedded = embed_search_svc(query=query, embeddings=container.embeddor)
        if query_embedded is None:
        # This is a return straight to the LLM, string representation is better
            return "Failed to embed the query"

        similar_products = similarity_search_svc(vector_query=query_embedded, vector_db=container.vector_db)
        if similar_products is None:
            return "Failed to fetched embedded query from database"

        result = [products.payload for products in similar_products if products.payload]
        logger.debug("Result of similar product payloads for agent", result=result)
        return result

    logger.info("Created All Tools")
    return [get_similar_products]

#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------

