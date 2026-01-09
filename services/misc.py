import logging
from concurrent.futures import ThreadPoolExecutor

from .internal.scraper import scrape_results_svc
from .internal.embeddor import embed_search_svc
from .internal.vector_db import similarity_search_svc

from agents.infrastructure.firecrawl_api.client import Scraper
from agents.infrastructure.vector_database.embeddings import Embeddor
from agents.infrastructure.vector_database.db import VectorDb
from agents.agent.llm import LLM


logger = logging.getLogger(__name__)

def search_products_comprehensive(query: str, scraper: Scraper, embeddor: Embeddor, vector_db: VectorDb, llm: LLM):
    logger.debug("Starting search_products_comprehensive", query=query)
    with ThreadPoolExecutor(max_workers=2) as executor:
        scraper_response = executor.submit(scrape_results_svc, query, scraper, llm)

        embeddings = embed_search_svc(query=query, embeddings=embeddor)
        if embeddings is None:
            raise ValueError("embeddings cant be none")
        search_response = executor.submit(similarity_search_svc, embeddings, vector_db)

        scraper_response_result = scraper_response.result()
        vector_result_result = search_response.result() if embeddings is not None else None


        logger.info("Completed search_products_comprehensive")
        return scraper_response_result, vector_result_result
