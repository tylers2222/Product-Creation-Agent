from product_agent.tools.vector_search import build_similar_products_tool

from product_agent.infrastructure.vector_db.embeddings import Embeddor
from product_agent.infrastructure.vector_db.client import VectorDb

def tools_for_synthesis_agent(embeddor: Embeddor, vector_db: VectorDb) -> list:
    """A function that builds all the tools for a specific agent"""
    return [
        build_similar_products_tool(embeddor=embeddor, vector_db=vector_db)
    ]
    