import logging

from agents.infrastructure.vector_database.embeddings import Embeddor

logger = logging.getLogger(__name__)

def embed_search_svc(query: str, embeddings: Embeddor) -> list[float] | None:
    logger.debug("", query=query, returned_embeddor=True)

    try:
        embedded_query = embeddings.embed_documents(documents = [query])
        logger.debug("Embedded Query Returned", query=query, embedded_query=embedded_query[:100])
        logger.info("Returned embeddings successfully")
        return embedded_query
    except Exception as embed_error:
        logger.error(f"Error obtaining embed from query", query=query, error=embed_error, stack_info=True)
        return None