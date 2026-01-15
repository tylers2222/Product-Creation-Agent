from pydantic import BaseModel, Field
from qdrant_client.models import PointStruct

from .scraper_response import ScraperResponse

class QuerySynthesis(BaseModel):
    """TODO"""
    web_scraped_data: ScraperResponse
    similar_products: list[PointStruct]

