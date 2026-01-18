from pydantic import BaseModel
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

class DataResult(BaseModel):
    markdown: str
    title: str | None
    description: str | None
    url: str | None

    @classmethod
    def validate_scrape(cls, scrape: dict) -> "DataResult":
        logger.debug("Starting validate_scrape method on DataResult")
        metadata = scrape.get("metadata", {})

        logger.debug("Completed validate_scrape")
        return cls(
            markdown = scrape.get("markdown", {}),
            title = metadata.get("title", {}),
            description = metadata.get("description", {}),
            url = metadata.get("url", {})
        )


class FireResult(BaseModel):
    data: Any  # SearchData from firecrawl.search() as its not importable
    query: str