from langgraph.graph import START, StateGraph, END
from typing import TypedDict
import os
from shopify_api.product_schema import DraftProduct
from .schema import ScraperResponse

class AgentState(TypedDict):
    query: str # the original query the user writes
    extract_query: str # the extracted query from hte LLM
    validated_data: dict # dictionary representation of the product and its internal data
    web_scraped_data: ScraperResponse # the result of the web scraping operation
    filled_data: DraftProduct # fill the draft struct with draft data
    shopify_response: dict


