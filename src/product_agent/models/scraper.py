from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

class ProcessedResult(BaseModel):
    """Model for tracking processing failures"""
    index: int
    error: str

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

    def markdowns_needings_summarisation(self):
        logger.debug("Starting markdowns_needings_summarisation")

        result = []
        for idx, markdown in enumerate(self.result):
            if len(markdown) > 15000:
                result.append({"idx": idx, "markdown": markdown})

        logger.debug("Length of markdowns that need summarising %s", len(result))
        return result

# -----------------------------------------------------------------------------------
class ScraperSynthesisResponse(BaseModel):
    """Structured output for LLM scrapes"""
    url:            str
    name:           str     | None
    price:          float   | None
    currency:       str     | None
    description:    str     | None
    other:          dict    | None = Field(description="Any drop down on a product page thats not description")
    image_urls:     list    | None
    sku:            str     | None
    brand:          str     | None
    category:       str     | None
    attributes:     dict    | None = Field(description="Products attributes like its usecase / features")
    rating:         float   | None
    review_count:   int     | None
    metadata:       dict    | None
