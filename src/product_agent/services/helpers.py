import logging
from concurrent.futures import ThreadPoolExecutor

from .scraping import scrape_results_svc
from .embedding import embed_search_svc
from .vector_search import similarity_search_svc

from product_agent.infrastructure.firecrawl.client import Scraper
from product_agent.infrastructure.vector_db.embeddings import Embeddor
from product_agent.infrastructure.vector_db.client import VectorDb
from product_agent.infrastructure.llm.client import LLM


logger = logging.getLogger(__name__)

def search_products_comprehensive(query: str, scraper: Scraper, embeddor: Embeddor, vector_db: VectorDb, llm: LLM):
    logger.debug("Starting search_products_comprehensive", query=query)
    with ThreadPoolExecutor(max_workers=2) as executor:
        scraper_response = executor.submit(scrape_results_svc, query, scraper, llm)

        embeddings = embed_search_svc(query=query, embeddings=embeddor)
        if embeddings is None:
            raise ValueError("embeddings cant be none")
        search_response = executor.submit(similarity_search_svc, vector_query=embeddings, results_wanted=4, vector_db=vector_db)

        scraper_response_result = scraper_response.result()
        vector_result_result = search_response.result()

        logger.info("Completed search_products_comprehensive")
        return scraper_response_result, vector_result_result
