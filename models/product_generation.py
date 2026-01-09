from pydantic import BaseModel, Field
from qdrant_client.models import PointStruct

from .scraper_response import ScraperResponse

# Pydantic models for responses
class QueryResponse(BaseModel):
    """Model that defines the first node of the product creation agent"""
    adapted_search_string: str = Field(description="A new and improved search string to get products on google, otherwise None")

class QuerySynthesis(BaseModel):
    """TODO"""
    web_scraped_data: ScraperResponse
    similar_products: list[PointStruct]

