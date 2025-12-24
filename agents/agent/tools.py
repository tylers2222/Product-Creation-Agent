from qdrant_client.models import PointStruct
from agents.infrastructure.firecrawl_api.client import FirecrawlClient, FireResult, Scraper
from agents.infrastructure.shopify_api.client import ShopifyClient, DraftProduct, Shop
from agents.infrastructure.vector_database.db import VectorDb, vector_database
from agents.infrastructure.vector_database.embeddings import Embeddings, Embeddor
from langchain.tools import tool
from .services import scrape_results_svc, embed_search_svc, similarity_search_svc, search_products_comprehensive
from .schema import ScraperResponse
from .llm import LLM
import logging
import traceback
from pydantic import BaseModel, Field
from typing import Optional
import structlog
import inspect
from dataclasses import dataclass

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(),
    ]
)
# Get the base logger
base_logger = structlog.get_logger()

@dataclass
class ServiceContainer:
    vector_db:  VectorDb
    embeddor:   Embeddor
    scraper:    Scraper
    shop:       Shop
    llm:        LLM

def create_all_tools(container: ServiceContainer) -> list:
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
        return result

    return [get_similar_products]

#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
