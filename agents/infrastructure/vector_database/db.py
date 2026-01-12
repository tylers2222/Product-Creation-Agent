import datetime
import logging
import traceback
import structlog
from typing import Protocol
from qdrant_client.models import PayloadSchemaType, PointStruct, FieldCondition, MatchValue, Filter, VectorParams, Distance
from qdrant_client import QdrantClient

from agents.infrastructure.vector_database.response_schema import DbResponse
from agents.infrastructure.vector_database.schema import VectorFilter

logger = structlog.get_logger(__name__)

class VectorDb(Protocol):
    """Defining the schema of the vector database"""
    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> DbResponse | None:
        ...
    def search_points(self, collection_name: str, query_vector: list[float], vector_filter: VectorFilter | None = None, k: int = 5) -> list:
        """query_vector = the vector we want to match to
            k = the number of results we want to return
        """
        ...

class vector_database:
    """Concrete vector database impl"""
    def __init__(self, api_url: str, api_key: str):
        logger.debug("Starting to initialise vector_database")

        self.client = QdrantClient(
            url=api_url, 
            api_key=api_key,
            timeout=3000
        )
        logger.info("Initialised vector_database")

    def get_collections(self):
        """List collections in current database"""
        # wont be used in interface satisfaction, a concrete only impl for testing
        logger.debug("Starting get_collections")
        return self.client.get_collection("shopify_products")

    def create_collection(self, collection_name: str, index_payload: bool = False, index_wanted: str | None = None):
        """
        Create a collection in the vector_database
        Does the database need indexing via the payload
        """
        logger.debug("Starting create_collection", collection_name=collection_name)
        created = self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
        if not created:
            logger.error("Failed to create collection", collection_name=collection_name)
            return created

        logger.info("Created Collection", collection_name=collection_name, indexing=index_payload)
        if index_payload:
            payload_index = self.create_payload_index(collection_name=collection_name, field_name=index_wanted) 
            logger.debug("Created payload_index", payload_index_response=payload_index.model_dump_json(), key=index_wanted)

        return created

    def delete_collection(self, collection_name: str):
        logger.debug("About to deleted collection", collection=collection_name)
        deleted = self.client.delete_collection(collection_name=collection_name)
        logger.info("Deleted collection", collection=collection_name)
        return deleted

    def search_points(self, 
        collection_name: str, 
        query_vector: list[float], 
        vector_filter: VectorFilter | None = None, 
        k: int = 5) -> list:
        # new method, return a Query Response object
        logger.debug("Starting search_points", collection_name=collection_name, query_vector_length=len(query_vector), filtering=vector_filter is not None)

        if vector_filter is not None:
            return self.client.query_points(
                collection_name=collection_name, 
                query=query_vector, 
                limit=k,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key=vector_filter.key,
                            match=MatchValue(value=vector_filter.value)
                        )
                    ]
                )).points

        return self.client.query_points(
                    collection_name=collection_name, 
                    query=query_vector, 
                    limit=k).points

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

    def create_payload_index(self, collection_name: str, field_name: str):
        """To search by a payload key, you need to first index it to stop 1M row searches"""
        return self.client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=PayloadSchemaType.KEYWORD
        )



