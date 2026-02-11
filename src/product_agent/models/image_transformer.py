from typing import Literal
from pydantic import BaseModel, Field

class Image(BaseModel):
    type: Literal["image"] = "image"
    url: str
    image_bytes: bytes

    def turn_to_bytes(self):
        return bytes(self.url, encoding="utf-8") + self.image_bytes

class Query(BaseModel):
    type: Literal["query"] = "query"
    query: str | bytes

    def turn_to_bytes(self):
        return bytes(self.query, encoding="utf-8")

class ImageTransformer(BaseModel):
    """
    Defines the order of a query that can be multiple types
    In relation to vision models or invoking with an image
    """
    order: list[Image | Query] = Field(description="The order of query for the LLM")

    def how_many_images(self) -> int:
        """Calculate how many images for processing"""
        result = 0
        for o in self.order:
            if o.type == "image":
                result += 1

        return result