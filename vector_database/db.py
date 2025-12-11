import datetime
import logging
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
import structlog

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from vector_database.response_schema import DbResponse

load_dotenv()
api_url = os.getenv("QDRANT_URL")
api_key = os.getenv("QDRANT_API_KEY")

# Setup structlog (simplified setup for key-value output)
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(),
    ]
)
base_logger = structlog.get_logger()

class VectorDb(Protocol):
    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        ...
    def search_points(self, collection_name: str, query_vector: list[float], k: int) -> list:
        """query_vector = the vector we want to match to
            k = the number of results we want to return
        """
        ...

class vector_database:
    def __init__(self):
        self.client = QdrantClient(
            url=api_url, 
            api_key=api_key,
            timeout=3000
        )

    def get_collections(self):
        # wont be used in interface satisfaction, a concrete only impl for testing
        return self.client.get_collection("shopify_products")

    def create_collection(self, collection_name: str):
        try:
            created = self.client.create_collection(collection_name=collection_name)
            if not created:
                logging.error(f"Failed to create collection {collection_name}")

        except Exception as e:
            logging.error(f"Failed to create collection {collection_name}: {e}")

    def search_points(self, collection_name: str, query_vector: list[float], k: int) -> list:
        # new method, return a Query Response object
        return self.client.query_points(collection_name=collection_name, query=query_vector, limit=k).points

    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        try:
            update_result = self.client.upsert(
                collection_name = collection_name,
                points = points,
            )

            if update_result.status == "completed":
                return DbResponse(
                    records_inserted=len(points),
                    collection_name=collection_name,
                    time=datetime.datetime.now(),
                    error=None,
                    traceback=None
                )
            else:
                logging.error(f"Upsert failed with status: {update_result.status}")
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



