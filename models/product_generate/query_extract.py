from pydantic import BaseModel, Field

class QueryResponse(BaseModel):
    """Model that defines the first node of the product creation agent"""
    adapted_search_string: str = Field(description="A new and improved search string to get products on google, otherwise the original string that went in")