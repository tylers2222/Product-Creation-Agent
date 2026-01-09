import logging

from agents.infrastructure.vector_database.db import VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddor

from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)

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
        logger.error(f"Error obtaining results from vector_db", vector_query=vector_query[:25], error=search_error, stack_info=True)
        return None

def batch_products_to_vector_db(products: list, database: VectorDb, embedder: Embeddor, collection_name: str):
    """Business Logic For Adding Products To Vector Db """
    logger.debug("Started batch_products_to_vector_db service", collection_name=collection_name, length_of_products=len(products))

    batch_size = 50
    batch_number = 1
    try:
        # These product titles are generated from an Agent currnetly or a product generation cycle
        # and is Brand Name + Product Name
        # If at scale this is used elsewhere, it needs to be brand name + product name for Evelyn Faye
        product_titles = [product.title for product in products]
        embeddings = embedder.embed_documents(documents=product_titles)
        if not embeddings:
            logger.error("no embeddings returned", stack_info=True)
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
                logger.error(f"Error Adding Vectors To Vector Db", error=db_resp.error, stack_info=True)            
                return None

            logger.debug("db_resp returned", db_resp=db_resp)
            batch_number += 1

        logger.info("Successfully Uploaded Vectors To Vector Database")
        return "Success" # will change this to be more professional shortly
    except Exception as e:
        logger.error(f"Error Adding Vectors To Vector Db", error=e, stack_info=True)
        return None
