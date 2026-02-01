from datetime import datetime
from pydantic import BaseModel
from .product import PromptVariant

class RequestSchema(BaseModel):
    request_id: str
    created_at: datetime
    body: PromptVariant

class Job(BaseModel):
    completed: bool
    time_completed: datetime | None = None
    url_of_job: str | None = None # Shopify URL returned
    error: str | None = None