from pydantic import BaseModel

class VectorRelevanceResponse(BaseModel):
    """A model to outline the node """
    relevance_score: int
    matches: int
    total: int
    action_taken: str
    reasoning: str
    similar_products: list[dict]