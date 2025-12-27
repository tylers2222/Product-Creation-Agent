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

    inventory_at_stores: InventoryAtStores | None = Field(description="If no inventory updates needed at time of request can be none")


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

