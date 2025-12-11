from pydantic import BaseModel, Field, computed_field, model_validator
from typing import List
import datetime


class Variant(BaseModel):
    """ A struct for individaul variants """
    option1_value: str = Field(description="A list of the option names -> example: all the sizes of the product")
    option2_value: str | None = None
    option3_value: str | None = None

    sku: int = Field(description="stock keeping unit, internal knowledge, will come from the query")
    barcode: int = Field(description="barcode, internal knowledge, will come from the query")

    price: float
    compare_at: float | None
    product_weight: float


class DraftProduct(BaseModel):
    """ The parent struct """

    title: str = Field(description="The products title that customers see, Brand Name -> Product Name -> NO size in the title")
    description: str = Field(description="Description of the prodcut, our own SEO optimised description in HTML for shopify")

    inventory: List[int] = Field(description="A list of 2 stores, always 1000,1000 for the moment")

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
        
        option1_values = list(dict.fromkeys(variant.option1_value for variant in self.variants))
        option.append(
            {
                "name": self.lead_option,
                "values": option1_values
            }
        )

        if self.baby_options and len(self.baby_options) > 0:
            option2_values = list(dict.fromkeys(variant.option2_value for variant in self.variants if variant.option2_value))
            option.append(
            {
                "name": self.baby_options[0],
                "values": option2_values
            }
        )

        if self.baby_options and len(self.baby_options) > 1:
            option3_values = list(dict.fromkeys(variant.option3_value for variant in self.variants if variant.option3_value))
            option.append(
            {
                "name": self.baby_options[1],
                "values": option3_values
            }
        )

        return option
        

# A response object for creating a product draft via the shopify Api
class DraftResponse(BaseModel):
    """A model for responses to creating shopify drafts """
    title: str
    url: str
    time_of_comepletion: datetime.datetime
    status_code: int | None


