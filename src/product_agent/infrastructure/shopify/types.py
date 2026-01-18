from pydantic import BaseModel
from typing import Literal

class Inputs(BaseModel):
    """A stores inventory input"""
    name_of_store: Literal["City", "South Melbourne"]
    inventory_number: int

class Inventory(BaseModel):
    """Model for inventory management related to graphQL"""
    inventory_item_id: str
    stores: list[Inputs] | None

    def all_stores(self, quantity_wanted: int):
        if self.stores is None:
            self.stores = [Inputs(name_of_store="City", inventory_number=quantity_wanted), Inputs(name_of_store="South Melbourne", inventory_number=quantity_wanted)]

    # could add a needs inventory and adjust inventory method on this
    # it would mean that inevtory could be none and we route to a database to get the number
    # example our internal inventory db
    # or route to admin acc on GUI for inventory input
        
class Product(BaseModel):
    "Product dict that holds title"
    title: str

class SkuSearchResponse(BaseModel):
    """Search response from shopify's graph ql"""
    sku: str
    product: Product