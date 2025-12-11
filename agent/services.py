from concurrent.futures import ThreadPoolExecutor
import os
import sys
from typing import Optional

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langchain_core import documents
from qdrant_client.models import PointStruct
from vector_database.db import VectorDb
import logging
import structlog
import inspect
import traceback
from vector_database.embeddings import Embeddor
from firecrawl_api.client import Scraper
from .llm_client import SummarisationError, markdown_summariser
from .schema import ScraperResponse, ProcessedResult

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(), # Renders to key=value pairs
    ]
)
# Get the base logger
base_logger = structlog.get_logger()

def add_products_to_vector_db(products: list, database: VectorDb, embedder: Embeddor, collection_name: str):
    """Business Logic For Adding Products To Vector Db """
    scoped_logs = base_logger.bind(function_name=inspect.stack()[0][3], collection_name=collection_name)
    batch_size = 50
    batch_number = 1

    try:
        product_titles = [product.title for product in products]
        embeddings = embedder.embed_documents(documents=product_titles)
        if not embeddings:
            scoped_logs.error("no embeddings returned")
            return None

        scoped_logs.info("Recieved Embeddings")

        for i in range(0, len(products), batch_size):
            scoped_logs.info(f"Starting Batch Number {batch_number} with size {batch_size}")
            batch_products = products[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]

            points = [
                PointStruct(
                    id=i+idx,  # Global ID across all batches
                    vector=vector,
                    payload={
                        "id": product.id,  
                        "title": product.title,
                        "body_html": product.body_html,
                        "product_type": product.product_type,
                        "tags": product.tags
                    }
                )
                for idx, (vector, product) in enumerate(zip(batch_embeddings, batch_products))
            ]

            db_resp = database.upsert_points(collection_name=collection_name, points=points)
            if not db_resp:
                scoped_logs.error("No database response on upsert")
                return None

            if db_resp.error is not None:
                scoped_logs.error(f"Error Adding Vectors To Vector Db: {db_resp.error} -> {traceback.format_exc()}")            
                return None
            batch_number += 1

        scoped_logs.info("Successfully Uploaded Vectors To Vector Database")
        return "Success" # will change this to be more professional shortly
    except Exception as e:
        scoped_logs.error(f"Error Adding Vectors To Vector Db: {e} -> {traceback.format_exc()}")
        return None


def scrape_results_svc(search_str: str, scraper: Scraper) -> ScraperResponse | None:
    try:
        scoped_logs = base_logger.bind(function_name=inspect.stack()[0][3], search_string_internet=search_str)

        # ----------------------------------------
        fire_result = scraper.scrape_and_search_site(query=search_str)
        scrapes_list = fire_result.data.web
        scoped_logs.info(f"Found {len(scrapes_list)} urls in the {search_str} search")

        tokens = 0
        data_result = []
        failures: list[ProcessedResult] = []
        for idx, scrapes in enumerate(scrapes_list):
            if hasattr(scrapes, "markdown"):
                mrkdown = scrapes.markdown
            else:
                scoped_logs.info(f"{idx} in the scrape loop didnt have a markdown")
                continue

            if not mrkdown:
                metadata = scrapes.metadata
                url = getattr(metadata, 'url', 'unknown') if metadata else 'unknown'
                scoped_logs.info(f"{url} didnt have markdown...")
                failures.append(ProcessedResult(index=idx, error="No markdown content"))
                continue

            tokens += len(mrkdown)
            if len(mrkdown) > 15000:
                try:
                    summarised_markdown = markdown_summariser(search_str, mrkdown)
                    data_result.append(summarised_markdown.content)

                except SummarisationError as s:
                    scoped_logs.warn("summarisation failed, adding full markdown")
                    data_result.append(mrkdown)
                    failures.append(ProcessedResult(index=idx, error=str(s)))
            else:
                data_result.append(mrkdown)
            
        token_estimate = tokens / 4
        return ScraperResponse(
            query = search_str,
            result = data_result,
            errors = failures if failures else None,
            all_failed = True if len(failures) == len(scrapes_list) else False,
            all_success = True if len(failures) == 0 else False
        )
        
    except Exception as e:
        scoped_logs.error(f"failed to scrape results: {e} -> {traceback.format_exc()}")
        return None


def embed_search_svc(query: str, embeddings: Embeddor) -> list[list[float]] | None:
    scoped_logs = base_logger.bind(function_name=inspect.stack()[0][3], query=query, returned_embeddor=True)

    try:
        embedded_query = embeddings.embed_documents(documents = [query])
        scoped_logs.info("Returned embeddings successfully")
        return embedded_query
    except Exception as embed_error:
        scoped_logs.error(f"Error obtaining embed from query -> {embed_error}\n\n{traceback.format_exc()}")
        return None

def similarity_search_svc(vector_query: list[float], vector_db: VectorDb) -> list[PointStruct] | None:
    scoped_logs = base_logger.bind(function_name=inspect.stack()[0][3], query=vector_query[0][:5] ,returned_db=True)

    try:
        points = vector_db.search_points(collection_name="shopify_products", query_vector=vector_query[0], k=3)
        if not points:
            scoped_logs.error("No search results returned for search vector")
            return None

        # return the whole points payload
        return points

    except Exception as search_error:
        scoped_logs.error(f"Error obtaining results from vector_db -> {search_error}\n\n{traceback.format_exc()}")
        return None

def search_products_comprehensive(query: str, scraper: Scraper, embeddor: Embeddor, vector_db: VectorDb):
    with ThreadPoolExecutor(max_workers=2) as executor:
        scraper_response = executor.submit(scrape_results_svc, query, scraper)

        embeddings = embed_search_svc(query=query, embeddings=embeddor)
        if embeddings is not None:
            search_response = executor.submit(similarity_search_svc, embeddings, vector_db)

        scraper_response_result = scraper_response.result()
        vector_result_result = search_response.result() if embeddings is not None else None

        return scraper_response_result, vector_result_result