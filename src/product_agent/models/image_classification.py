from pydantic import BaseModel, Field

class ImageRelevanceResponse(BaseModel):
    """Image Classification Relevance Response"""
    query:      str
    url:        str | None = Field(description="The url if an image matched")
    reason:     str = Field(description="Analysis of the images if they did or didnt match and why/why not?")
    confidence: int = Field(description="Confidence score out of 10")