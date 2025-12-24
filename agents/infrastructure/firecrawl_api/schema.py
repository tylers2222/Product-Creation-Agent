from pydantic import BaseModel
from typing import Any

class DataResult(BaseModel):
    markdown: str
    title: str | None
    description: str | None
    url: str | None

    @classmethod
    def validate_scrape(cls, scrape: dict) -> "DataResult":
        metadata = scrape.get("metadata", {})

        return cls(
            markdown = scrape.get("markdown", {}),
            title = metadata.get("title", {}),
            description = metadata.get("description", {}),
            url = metadata.get("url", {})
        )


class FireResult(BaseModel):
    data: Any  # SearchData from firecrawl.search() as its not importable
    query: str