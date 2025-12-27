from dataclasses import dataclass
from dotenv import load_dotenv
import os

from agents.infrastructure.firecrawl_api.client import FirecrawlClient, Scraper
from agents.infrastructure.shopify_api.client import ShopifyClient, Shop, Locations, Location
from agents.infrastructure.vector_database.db import vector_database, VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddings, Embeddor
from agents.agent.llm import LLM, llm_client

load_dotenv()

@dataclass
class ServiceContainer:
    shop: Shop
    scraper: Scraper
    vector_db: VectorDb
    embeddor: Embeddor
    llm: LLM

def create_service_container() -> ServiceContainer:
    locations = Locations(
        locations=[
            Location(name="City", id=f"gid://shopify/Location/{os.getenv("LOCATION_ONE_ID")}"),
            Location(name="South Melbourne", id=f"gid://shopify/Location/{os.getenv("LOCATION_TWO_ID")}")
        ]
    )
    
    shop = ShopifyClient(
        api_key = os.getenv("SHOPIFY_API_KEY"),
        api_secret = os.getenv("SHOPIFY_API_SECRET"),
        token = os.getenv("SHOPIFY_TOKEN"),
        shop_name = os.getenv("SHOP_NAME"),
        shop_url = os.getenv("SHOP_URL"),
        locations=locations
    )

    scraper = FirecrawlClient(api_key=os.getenv("FIRECRAWL_API_KEY"))
    vector_db = vector_database(api_url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    embeddor = Embeddings()
    llm = llm_client()

    return ServiceContainer(
        shop=shop,
        scraper=scraper,
        vector_db=vector_db,
        embeddor=embeddor,
        llm=llm
    )