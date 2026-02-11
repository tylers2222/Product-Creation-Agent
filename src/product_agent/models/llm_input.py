from typing import Type
from pydantic import BaseModel

class LLMInput(BaseModel):
    """Schema for LLM inputs"""
    model: str
    system_query: str | None = None
    user_query: str | list
    response_schema: Type[BaseModel] | None = None
    verbose: bool = False
    cache_wanted: bool = False
