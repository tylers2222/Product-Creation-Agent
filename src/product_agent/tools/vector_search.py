import structlog
from langchain.tools import tool

from product_agent.services.infrastructure.embedding import embed_search_svc
from product_agent.services.infrastructure.vector_search import similarity_search_svc

from product_agent.infrastructure.vector_db.embeddings import Embeddor
from product_agent.infrastructure.vector_db.client import VectorDb

logger = structlog.getLogger(__name__)

def build_similar_products_tool(embeddor: Embeddor, vector_db: VectorDb):
    @tool
    def get_similar_products(query: str):
        """
        Search the vector database for products similar to the query.

        Use this when the current similar products don't match the target category.
        Use generic category names, not brand names.

        Args:
            query: Product category to search for (e.g., "pre-workout supplement")

        Returns:
            List of similar products from the store's catalog
        """
        query_embedded = embed_search_svc(query=query, embeddings=embeddor)
        if query_embedded is None:
            return "Failed to embed the query"

        similar_products = similarity_search_svc(
            vector_query=query_embedded,
            results_wanted=5,
            vector_db=vector_db
        )
        if similar_products is None:
            return "Failed to fetch similar products from database"

        result = [p.payload for p in similar_products if p.payload]
        logger.debug("get_similar_products tool result", count=len(result))
        return result

    return get_similar_products