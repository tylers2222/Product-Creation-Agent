from pydantic import BaseModel
from typing import Literal

class Inputs(BaseModel):
    """A stores inventory input"""
    name_of_store: Literal["City", "South Melbourne"]
    inventory_number: int

class Inventory(BaseModel):
    """Model for inventory management"""
    inventory_item_id: str
    stores: list[Inputs]

    # could add a needs inventory and adjust inventory method on this
    # it would mean that inevtory could be none and we route to a database to get the number
    # example our internal inventory db
    # or route to admin acc on GUI for inventory input
        
