from pydantic import BaseModel, Field, computed_field, model_validator
from typing import List
import datetime

from .schema import Inventory

class Option(BaseModel):
    option_name: str
    option_value: str

class InventoryAtStores(BaseModel):
    city: int | None
    south_melbourne: int | None

    #@model_validator(mode="after")
    #def check_both_not_none(self):
    #    if self.city is None and self.south_melbourne is None:
    #        raise ValueError("All stores return no desired inventory set")

    #    return self

class Variant(BaseModel):
    """ A struct for individaul variants """
    option1_value: Option = Field(description="A list of the option names -> example: all the sizes of the product")
    option2_value: Option | None = None
    option3_value: Option | None = None
    
    sku: int = Field(description="stock keeping unit, internal knowledge")
    barcode: int = Field(description="barcode, internal knowledge")
    
    price: float
    compare_at: float | None = None
    product_weight: float

    inventory_at_stores: InventoryAtStores | None = None


class DraftProduct(BaseModel):
    """ The parent struct """

    title: str = Field(description="The products title that customers see, Brand Name -> Product Name -> NO size in the title")
    description: str = Field(description="Description of the prodcut, our own SEO optimised description in HTML for shopify")

    # will add rag to this, to see what other similar products are doing in these fields
    type: str = Field(description="type of product, is it a Probiotic, Protein Powder, Tea")
    vendor: str = Field(description="the brand name of the product")
    tags: List[str] = Field(description="a few tags about the  product -> Valerian, Teas, Sleeping Disorders & Support Sleep Support, Lemon Verbena, Lavender, Chamomile")

    lead_option: str = Field(description="the parent variant type if size and flavours, people browse by size and then choose their flavour")
    baby_options: list[str] | None = None
    variants: List[Variant]

    @model_validator(mode="after")
    def validate_length(self):
        if self.baby_options is not None and len(self.variants) < len(self.baby_options):
            raise ValueError("Number Of Variants is less than athe proposed amount of options")
        
        if self.baby_options is None and len([variant.option2_value for variant in self.variants if variant.option2_value is not None]) > 0:
            raise ValueError("No baby options but more than 1 option in variants found")
        return self

    @computed_field
    @property
    def options(self) -> list[dict]:
        option = []
        
        option1_values = list(dict.fromkeys(variant.option1_value.option_value for variant in self.variants))
        option.append(
            {
                "name": self.lead_option,
                "values": option1_values
            }
        )

        baby_options = self.baby_options
        if baby_options is not None and len(baby_options) > 0:
            option2_values = list(dict.fromkeys(variant.option2_value.option_value for variant in self.variants if variant.option2_value))
            option.append(
                {
                    "name": baby_options[0],  # type: ignore[index]
                    "values": option2_values
                }
            )

        if baby_options is not None and len(baby_options) > 1:
            option3_values = list(dict.fromkeys(variant.option3_value.option_value for variant in self.variants if variant.option3_value))
            option.append(
                {
                    "name": baby_options[1],  # type: ignore[index]
                    "values": option3_values
                }
            )

        return option

# A response object for creating a product draft via the shopify Api
class DraftResponse(BaseModel):
    """A model for responses to creating shopify drafts """
    title: str
    id: str
    variant_inventory_item_ids: list[Inventory]
    url: str
    time_of_comepletion: datetime.datetime
    status_code: int | None


# ------------------------------------------------------------------
# Converting Shopify's terrible resource return into pydantic model
# ------------------------------------------------------------------


class ShopifyVariantSchema(BaseModel):
    """Pydantic model for a Shopify variant retrieved from the store."""
    id: int | None
    product_id: int | None
    title: str | None
    price: str | None
    sku: str | None = None
    barcode: str | None = None
    position: int
    inventory_item_id: int | None = None
    option1: str | None = None
    option2: str | None = None
    option3: str | None = None
    weight: float | None = None
    weight_unit: str | None = None

    @classmethod
    def from_shopify_resource(cls, resource) -> "ShopifyVariantSchema":
        """Convert a shopify.Variant resource to a Pydantic model."""
        return cls(
            id=resource.id,
            product_id=getattr(resource, "product_id", None),
            title=resource.title,
            price=resource.price,
            sku=getattr(resource, 'sku', None),
            barcode=getattr(resource, 'barcode', None),
            position=resource.position,
            inventory_item_id=getattr(resource, 'inventory_item_id', None),
            option1=getattr(resource, 'option1', None),
            option2=getattr(resource, 'option2', None),
            option3=getattr(resource, 'option3', None),
            weight=getattr(resource, 'weight', None),
            weight_unit=getattr(resource, 'weight_unit', None),
        )


class ShopifyProductSchema(BaseModel):
    """Pydantic model for a Shopify product retrieved from the store."""
    id: int | None
    title: str | None
    body_html: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    tags: str | None = None
    status: str | None = None
    variants: List[ShopifyVariantSchema] = Field(default_factory=list)

    @classmethod
    def from_shopify_resource(cls, resource) -> "ShopifyProductSchema":
        """Convert a shopify.Product resource to a Pydantic model."""
        variants = []
        if hasattr(resource, 'variants') and resource.variants:
            variants = [
                ShopifyVariantSchema.from_shopify_resource(v)
                for v in resource.variants
            ]

        return cls(
            id=resource.id,
            title=resource.title,
            body_html=getattr(resource, 'body_html', None),
            vendor=getattr(resource, 'vendor', None),
            product_type=getattr(resource, 'product_type', None),
            tags=getattr(resource, 'tags', None),
            status=getattr(resource, 'status', None),
            variants=variants,
        )

class Fields(BaseModel):
    """Specify tags for obtaining shopify products"""
    id:             bool | None = None
    title:          bool | None = None
    body_html:      bool | None = None
    category:       bool | None = None
    vendor:         bool | None = None
    product_type:   bool | None = None
    collections:    bool | None = None
    tags:           bool | None = None
    status:         bool | None = None

    def shopify_transform_fields(self) -> str:
        """Shopify require a string in a specific format"""
        result = ""
        for field in self.model_fields_set:
            result += f"{field}, "

        return result.strip()[:-1]

class AllShopifyProducts(BaseModel):
    """A list containing all the products returned"""
    products: List[ShopifyProductSchema]