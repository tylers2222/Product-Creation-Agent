from pydantic import BaseModel
from product_agent.infrastructure.shopify.schemas import Variant

class PromptVariant(BaseModel):
    """Schema for variant data when using format_product_input helper"""
    brand_name: str
    product_name: str

    variants: list[Variant]