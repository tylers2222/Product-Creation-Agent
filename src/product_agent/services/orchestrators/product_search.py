"""Product search orchestrator that coordinates scraping, embedding, and vector search services."""

import logging
from concurrent.futures import ThreadPoolExecutor

from product_agent.infrastructure.firecrawl.client import Scraper
from product_agent.infrastructure.vector_db.embeddings import Embeddor
from product_agent.infrastructure.vector_db.client import VectorDb
from product_agent.infrastructure.llm.client import LLM

from ..infrastructure.scraping import scrape_results_svc
from ..infrastructure.embedding import embed_search_svc
from ..infrastructure.vector_search import similarity_search_svc

logger = logging.getLogger(__name__)


def search_products_comprehensive(query: str, scraper: Scraper, embeddor: Embeddor, vector_db: VectorDb, llm: LLM):
    """
    Orchestrates a comprehensive product search by coordinating multiple services in parallel.

    This orchestrator runs web scraping and vector similarity search concurrently to gather
    product information from both live web sources and stored vector embeddings.

    Args:
        query: Search query string for products
        scraper: Scraper client for web scraping
        embeddor: Embeddings client for converting text to vectors
        vector_db: Vector database client for similarity search
        llm: LLM client (currently unused but passed for consistency)

    Returns:
        Tuple of (scraper_response, vector_search_results)
    """
    logger.debug("Starting search_products_comprehensive", query=query)
    with ThreadPoolExecutor(max_workers=2) as executor:
        scraper_response = executor.submit(scrape_results_svc, query, scraper)

        embeddings = embed_search_svc(query=query, embeddings=embeddor)
        if embeddings is None:
            raise ValueError("embeddings cant be none")
        search_response = executor.submit(similarity_search_svc, vector_query=embeddings, results_wanted=4, vector_db=vector_db)

        scraper_response_result = scraper_response.result()
        vector_result_result = search_response.result()

        logger.info("Completed search_products_comprehensive")
        return scraper_response_result, vector_result_result
