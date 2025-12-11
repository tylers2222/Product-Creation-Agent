from qdrant_client.models import PointStruct
from firecrawl_api.client import FirecrawlClient, FireResult, Scraper
from shopify_api.client import ShopifyClient, DraftProduct, Shop
from vector_database.db import VectorDb, vector_database
from vector_database.embeddings import Embeddings, Embeddor
from langchain.tools import tool
from agent.llm_client import llm
from agent.services import scrape_results_svc, embed_search_svc, similarity_search_svc, search_products_comprehensive
from agent.schema import ScraperResponse
import logging
import traceback
from pydantic import BaseModel, Field
from typing import Optional
import structlog
import inspect

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(),
    ]
)
# Get the base logger
base_logger = structlog.get_logger()

def _get_scraper() -> Scraper:
    return FirecrawlClient()

def _get_shop() -> Shop:
    return ShopifyClient()

def _get_db() -> VectorDb:
    return vector_database()

def _get_embeddor() -> Embeddor:
    return Embeddings()

class ScrapeAndSimilarityResponse(BaseModel):
    scraper_response: ScraperResponse | None
    similarity_response: list[dict] | None = Field(description="pass the payload not the full pointstruct for token saving")
    
@tool
def web_scraper_and_similarity_searcher(query: str) -> ScrapeAndSimilarityResponse | None:
    """
Web scraping tool that searches a query and returns page markdown and other relevatn data

It also returns a list of products from our current store to give a guidance of how similar products are input

MUST BE USED BEFORE A PRODUCT DRAFTER
    """
    # in time potentially add some query must include using strings lib
    # example query must contain SKU etc
    return scrape_and_return_similar_products(query=query, scraper=None, embeddor=None, vector_db=None)


@tool
def product_drafter(product_listing: DraftProduct):
    """
Product drafting tool that takes in a product listing structs and sends a post request to shopify's api

MUST NOT BE USED WITHOUT the web_scraper tool first
    """
    return draft_product_impl(product_listing=product_listing, shop=None)

#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------


def scrape_and_return_similar_products(query: str, scraper: Optional[Scraper], embeddor: Optional[Embeddor], vector_db: Optional[VectorDb]) -> ScrapeAndSimilarityResponse | None:
    """
    CRITICAL: Call this tool EXACTLY ONCE per user request, regardless of how many variants requested.
    
    Search for product information using ONLY brand + product name.
    DO NOT include size/flavor/variant details in the query.
    
    Example queries:
    ✅ "Optimum Nutrition Gold Standard Whey Protein"
    ❌ "Optimum Nutrition Gold Standard Whey 5lbs Chocolate"
    
    Returns scraped data from ~5 websites plus similar products from vector DB.
    Use the returned data to create ALL variants the user requested.
    """ 
    if scraper is None:
        scraper = _get_scraper()

    if embeddor is None:
        embeddor = _get_embeddor()

    if vector_db is None:
        vector_db = _get_db()

    scraper_response, vector_search_response = search_products_comprehensive(query=query, scraper=scraper, embeddor=embeddor, vector_db=vector_db)
    if scraper_response is None:
        return None
    if vector_search_response is None:
        return ScrapeAndSimilarityResponse(scraper_response=scraper_response, similarity_response=None)

    return ScrapeAndSimilarityResponse(scraper_response=scraper_response, similarity_response=[resp.payload for resp in vector_search_response])

def web_scraper_impl(query: str, scraper: Optional[Scraper]) -> ScraperResponse | None:
    """A web scraping impl that helps the Agent get the concrete scraper, it cant in a tool wrapped function"""
    if scraper is None:
        scraper = _get_scraper()
        
    # Can either return Scraper Result or None
    return scrape_results_svc(search_str=query, scraper=scraper)
    

def embed_query(query: str, embeddings: Optional[Embeddor]) -> list[list[float]] | None:
        if embeddings is None:
            embeddings = _get_embeddor()

        return embed_search_svc(query=query, embeddings=embeddings)


def similarity_search(vector_query: list[float], vector_db: Optional[VectorDb]) -> list[PointStruct] | None:
    if vector_db is None:
        vector_db = _get_db()

    return similarity_search_svc(vector_query=vector_query, vector_db=vector_db)



def draft_product_impl(product_listing: DraftProduct, shop: Optional[Shop]):
    if shop is None:
        shop = _get_shop()

    try:
        return shop.make_a_product_draft(product_listing=product_listing)

    except Exception as e:
        return str(e)