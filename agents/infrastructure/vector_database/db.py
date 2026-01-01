import datetime
import logging
import structlog
import traceback
from typing import Protocol
from numpy.core import records
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct
from typing import Optional
from dotenv import load_dotenv
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.infrastructure.vector_database.response_schema import DbResponse

logger = structlog.get_logger(__name__)

class VectorDb(Protocol):
    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        ...
    def search_points(self, collection_name: str, query_vector: list[float], k: int) -> list:
        """query_vector = the vector we want to match to
            k = the number of results we want to return
        """
        ...

class vector_database:
    def __init__(self, api_url: str, api_key: str):
        logger.debug("Starting to initialise vector_database")

        self.client = QdrantClient(
            url=api_url, 
            api_key=api_key,
            timeout=3000
        )
        logger.info("Initialised vector_database")

    def get_collections(self):
        # wont be used in interface satisfaction, a concrete only impl for testing
        logger.debug("Starting get_collections")
        return self.client.get_collection("shopify_products")

    def create_collection(self, collection_name: str):
        logger.debug("Starting create_collection", collection_name=collection_name)
        try:
            created = self.client.create_collection(collection_name=collection_name)
            if not created:
                logger.error("Failed to create collection", collection_name=collection_name)

        except Exception as e:
            logger.error(f"Failed to create collection", collection_name=collection_name, error=e)

    def search_points(self, collection_name: str, query_vector: list[float], k: int) -> list:
        # new method, return a Query Response object
        logger.debug("Starting search_points", collection_name=collection_name, query_vector=query_vector[:10])
        return self.client.query_points(collection_name=collection_name, query=query_vector, limit=k).points

    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        logger.debug("Starting upsert_points", collection_name=collection_name, length_of_upsert=len(points))
        try:
            update_result = self.client.upsert(
                collection_name = collection_name,
                points = points,
            )

            logger.debug("Vector Upsert Result", update_result=update_result.model_dump_json())

            if update_result.status == "completed":
                logger.info("Completed Upsert Into Vector Db", collection_name=collection_name)
                return DbResponse(
                    records_inserted=len(points),
                    collection_name=collection_name,
                    time=datetime.datetime.now(),
                    error=None,
                    traceback=None
                )
            else:
                logger.error(f"Upsert failed with status: {update_result.status}")
                return DbResponse(
                    records_inserted=0,
                    collection_name=collection_name,
                    time=datetime.datetime.now(),
                    error=f"Upsert status: {update_result.status}",
                    traceback=None
                )
        

        except Exception as e:
            return DbResponse(
                records_inserted=0,
                collection_name=collection_name,
                time=datetime.datetime.now(),
                error=str(e),
                traceback=traceback.format_exc()
            )



