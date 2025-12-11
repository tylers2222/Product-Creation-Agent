from dataclasses import field
import datetime
from pydantic import BaseModel, Field

class DbResponse(BaseModel):
    records_inserted: int = Field(description="How many vectors inserted into the db")
    collection_name: str = Field(description="Name of the colleciton we are inserting the vectors into")
    time: datetime.datetime
    error: str | None
    traceback: str | None