from typing import Literal
from pydantic import BaseModel

class ProductExists(BaseModel):
    """Returned by function that checks for products existence"""
    product_name:       str
    score:              float | None = None
    sku:                int | None = None
    method:             Literal["shopify", "vector_search"]
