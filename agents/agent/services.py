from concurrent.futures import ThreadPoolExecutor
import os
import sys
from typing import Optional
import structlog
import logging
import inspect
import traceback

from langchain_openai import ChatOpenAI

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langchain_core import documents
from qdrant_client.models import PointStruct
from agents.infrastructure.vector_database.db import VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddor
from agents.infrastructure.firecrawl_api.client import Scraper
from .schema import ScraperResponse, ProcessedResult
from agents.infrastructure.shopify_api.client import Shop
from agents.infrastructure.shopify_api.product_schema import DraftProduct, DraftResponse
from .llm import LLM, markdown_summariser

logger = structlog.get_logger(__name__)

def add_products_to_vector_db(products: list, database: VectorDb, embedder: Embeddor, collection_name: str):
    """Business Logic For Adding Products To Vector Db """
    logger.debug("Started add_products_to_vector_db service", collection_name=collection_name, length_of_products=len(products))
    batch_size = 50
    batch_number = 1

    try:
        product_titles = [product.title for product in products]
        embeddings = embedder.embed_documents(documents=product_titles)
        if not embeddings:
            logger.error("no embeddings returned")
            return None

        logger.debug("Length of embeddings recieved: %s", len(embeddings))
        logger.info("Recieved Embeddings")

        for i in range(0, len(products), batch_size):
            logger.info("Starting Batch", batch_number=batch_number, batch_size=batch_size)
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
                logger.error("No database response on upsert")
                return None

            if db_resp.error is not None:
                logger.error(f"Error Adding Vectors To Vector Db: {db_resp.error} -> {traceback.format_exc()}")            
                return None

            logger.debug("db_resp returned", db_resp=db_resp)
            batch_number += 1

        logger.info("Successfully Uploaded Vectors To Vector Database")
        return "Success" # will change this to be more professional shortly
    except Exception as e:
        logger.error(f"Error Adding Vectors To Vector Db: {e} -> {traceback.format_exc()}")
        return None


def scrape_results_svc(search_str: str, scraper: Scraper, llm: LLM) -> ScraperResponse | None:
    logger.debug("Starting scrape_results_svc service", search_string_internet=search_str)
    try:
        fire_result = scraper.scrape_and_search_site(query=search_str)
        scrapes_list = fire_result.data.web
        logger.info(f"Found {len(scrapes_list)} urls in the {search_str} search")

        tokens = 0
        data_result = []
        failures: list[ProcessedResult] = []
        for idx, scrapes in enumerate(scrapes_list):
            if hasattr(scrapes, "markdown"):
                mrkdown = scrapes.markdown
            else:
                logger.info(f"{idx} in the scrape loop didnt have a markdown")
                continue

            if not mrkdown:
                metadata = scrapes.metadata
                url = getattr(metadata, 'url', 'unknown') if metadata else 'unknown'
                logger.warn("URL didnt have markdown...", url=url)
                failures.append(ProcessedResult(index=idx, error="No markdown content"))
                continue

            tokens += len(mrkdown)
            if len(mrkdown) > 15000:
                try:
                    summarised_markdown = markdown_summariser(title=search_str, markdown=mrkdown, llm=llm)
                    data_result.append(summarised_markdown)

                except AttributeError as a:
                    raise AttributeError(a)

                except TypeError as t:
                    raise TypeError(t)

                except Exception as e:
                    logger.warn(f"summarisation failed, adding full markdown", error=e)
                    data_result.append(mrkdown)
                    failures.append(ProcessedResult(index=idx, error=str(e)))
            else:
                data_result.append(mrkdown)
        
        logger.info("Completed scrape_results_svc")
        token_estimate = tokens / 4
        return ScraperResponse(
            query = search_str,
            result = data_result,
            errors = failures if failures else None,
            all_failed = True if len(failures) == len(scrapes_list) else False,
            all_success = True if len(failures) == 0 else False
        )
        
    except Exception as e:
        logger.error(f"failed to scrape results: -> {traceback.format_exc()}", error=e, search_str=search_str)
        return None


def embed_search_svc(query: str, embeddings: Embeddor) -> list[float] | None:
    logger.debug("", query=query, returned_embeddor=True)

    try:
        embedded_query = embeddings.embed_documents(documents = [query])
        logger.debug("Embedded Query Returned", query=query, embedded_query=embedded_query[:100])
        logger.info("Returned embeddings successfully")
        return embedded_query
    except Exception as embed_error:
        logger.error(f"Error obtaining embed from query -> {traceback.format_exc()}", query=query, error=embed_error)
        return None

def similarity_search_svc(vector_query: list[float], vector_db: VectorDb) -> list[PointStruct] | None:
    logger.debug("Started similarity_search_svc", query=vector_query[0][:5], returned_db=True)

    try:
        points = vector_db.search_points(collection_name="shopify_products", query_vector=vector_query[0], k=3)
        if not points:
            logger.error("No search results returned for search vector")
            return None

        # return the whole points payload
        logger.debug("similarity_search_svc points", points_list=points)
        logger.info("Completed similarity_search_svc", length_points_list=len(points))
        return points

    except Exception as search_error:
        logger.error(f"Error obtaining results from vector_db -> {search_error}\n\n{traceback.format_exc()}", vector_query=vector_query[:25])
        return None

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

def shop_svc(draft_product: DraftProduct, shop: Shop) -> DraftResponse:
    # add any business logic that pops up here later
    # log the draft at info level for an overall check what may have gone wrong very quickly in the final result
    logger.info("Sending Draft", draft=draft_product.model_dump_json())
    return shop.make_a_product_draft(product_listing=draft_product)


class ShopifyProductCreateService:
    def __init__(self, shop: Shop, scraper: Scraper, vector_db: VectorDb, embeddor: Embeddor, llm: LLM, tools: list):
        self.llm = llm
        self.shop = shop
        self.scraper = scraper
        self.vector_db = vector_db
        self.embeddor = embeddor

    def query_extract(request_id: str, query: PromptVariant):
        request_id = state.get("request_id", None)
        logger.debug("Starting query_extract node for request %s", request_id)

        query_model = state.get("query", None)
        if query_model is None:
            logger.error("Query coming in, has a none model", state=state)
            raise ValueError("Query coming in, has a none model")

        query_model.brand_name = query_model.brand_name.title()
        query_model.product_name = query_model.product_name.title()

        parser = PydanticOutputParser(pydantic_object=QueryResponse)
        format_instructions = parser.get_format_instructions()
        
        prompt = f"""
STEP 1: Synthesise the incoming request for google search

If you think {query_model.brand_name} {query_model.product_name}
Is going to produce the best google results, leave it as is {query_model.brand_name} {query_model.product_name}, otherwise formulate the best string to search

{format_instructions}
"""
        llm_response = self.llm.invoke_mini(system_query = None, user_query=prompt)
        query_response = parser.parse(llm_response)

        logger.debug("query_response: %s", query_response, request_id=request_id)
        logger.info("Completed query_extract", request_id=request_id)

        