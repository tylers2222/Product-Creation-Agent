from pydantic import BaseModel
from agents.infrastructure.shopify_api.product_schema import Variant

class PromptVariant(BaseModel):
    """Schema for variant data when using format_product_input helper"""
    brand_name: str
    product_name: str

    variants: list[Variant]