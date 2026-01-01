"""
Standalone data models for Evelyn Faye GUI
Copied from the main project to make GUI independent
"""
from pydantic import BaseModel, Field, model_validator
from typing import List


class Option(BaseModel):
    """Product option (e.g., Size: 50g, Flavor: Chocolate)"""
    option_name: str
    option_value: str


class InventoryAtStores(BaseModel):
    """Inventory levels at different store locations"""
    city: int | None
    south_melbourne: int | None


class Variant(BaseModel):
    """A single product variant with its properties"""
    option1_value: Option = Field(description="Primary option (e.g., Size)")
    option2_value: Option | None = None
    option3_value: Option | None = None
    
    sku: int = Field(description="Stock keeping unit")
    barcode: str = Field(description="Product barcode")  # Changed to str to match backend
    
    price: float
    compare_at: float | None = None
    product_weight: float
    
    inventory_at_stores: InventoryAtStores | None = Field(
        description="Inventory levels (optional)"
    )


class PromptVariant(BaseModel):
    """Schema for product data when submitting to API"""
    brand_name: str
    product_name: str
    variants: list[Variant]


def format_product_input(prompt_variant: PromptVariant) -> str:
    """
    Format product information for API submission
    
    Args:
        prompt_variant: PromptVariant object containing brand, product name, and variants
    
    Returns:
        Formatted string for the API
    """
    lines = [f"Create a draft product for {prompt_variant.product_name} by {prompt_variant.brand_name}"]
    lines.append("")
    lines.append("VARIANTS:")
    
    for idx, variant in enumerate(prompt_variant.variants, 1):
        parts = []
        
        # Add options
        if variant.option1_value:
            parts.append(f"{variant.option1_value.option_name}: {variant.option1_value.option_value}")
        if variant.option2_value:
            parts.append(f"{variant.option2_value.option_name}: {variant.option2_value.option_value}")
        if variant.option3_value:
            parts.append(f"{variant.option3_value.option_name}: {variant.option3_value.option_value}")
        
        # Add SKU, Barcode, Price
        parts.append(f"SKU: {variant.sku}")
        parts.append(f"Barcode: {variant.barcode}")
        parts.append(f"Price: ${variant.price:.2f}")
        
        # Add inventory if present
        if variant.inventory_at_stores:
            inv_parts = []
            if variant.inventory_at_stores.city is not None:
                inv_parts.append(f"city={variant.inventory_at_stores.city}")
            if variant.inventory_at_stores.south_melbourne is not None:
                inv_parts.append(f"south_melbourne={variant.inventory_at_stores.south_melbourne}")
            if inv_parts:
                parts.append(f"Inventory: {', '.join(inv_parts)}")
        
        variant_line = f"  {idx}. {', '.join(parts)}"
        lines.append(variant_line)
    
    return "\n".join(lines)

