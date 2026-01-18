import structlog

from product_agent.infrastructure.vector_db.embeddings import Embeddor

logger = structlog.getLogger(__name__)

def embed_search_svc(query: str, embeddings: Embeddor) -> list[float] | None:
    """Embeddings in the service layer"""
    logger.debug("", query=query, returned_embeddor=embeddings is not None)

    embedded_query = embeddings.embed_document(document=query)
    logger.debug("Embedded Query Returned", query=query, embedded_query=embedded_query[:100])
    logger.info("Returned embeddings successfully")
    return embedded_query