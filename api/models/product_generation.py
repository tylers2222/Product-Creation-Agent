from pydantic import BaseModel

class Option(BaseModel):
  option_name: str
  option_value: str

class Variant(BaseModel):
  option_1: Option
  option_2: Option | None = None
  option_3: Option | None = None
  sku: int
  barcode: str
  price: float

class PromptVariant(BaseModel):
    """Schema for variant data when using format_product_input helper"""
    brand_name: str
    product_name: str

    variants: list[Variant]