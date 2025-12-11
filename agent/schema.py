from pydantic import BaseModel, Field

"""A response schema for an agent in the product drafting workflow"""
class InvokeResponse(BaseModel):
    result:         dict | None
    total_tokens:   float
    total_cost:     float

class ProcessedResult(BaseModel):
    index: int
    error: str

class ScraperResponse(BaseModel):
    query:          str
    result:         list[str] = Field(description="A list of markdowns based on the product")
    errors:         list[ProcessedResult] | None
    all_failed:     bool
    all_success:    bool