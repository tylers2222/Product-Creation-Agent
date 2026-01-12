from dataclasses import dataclass
from dotenv import load_dotenv
import os

from agents.infrastructure.firecrawl_api.client import FirecrawlClient, Scraper
from agents.infrastructure.firecrawl_api.mock import MockScraperClient
from agents.infrastructure.shopify_api.client import ShopifyClient, Shop, Locations, Location
from agents.infrastructure.shopify_api.mock import MockShop
from agents.infrastructure.vector_database.db import vector_database, VectorDb
from agents.infrastructure.vector_database.db_mock import MockVectorDb
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

def create_mock_service_container():


def create_scraper():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    return FirecrawlClient(api_key=api_key)

def create_shop() -> ShopifyClient:
    api_key = os.getenv("SHOPIFY_API_KEY")
    api_secret = os.getenv("SHOPIFY_API_SECRET")
    token = os.getenv("SHOPIFY_TOKEN")
    shop_name = os.getenv("SHOP_NAME")
    shop_url = os.getenv("SHOP_URL")
    locations = Locations(
        locations=[
            Location(name="City", id=f"gid://shopify/Location/{os.getenv("LOCATION_ONE_ID")}"),
            Location(name="South Melbourne", id=f"gid://shopify/Location/{os.getenv("LOCATION_TWO_ID")}")
        ]
    )
    return ShopifyClient(api_key=api_key, api_secret=api_secret, token=token, shop_url=shop_url, shop_name=shop_name, locations=locations)

def create_vector_database() -> vector_database:
    vector_database_url = os.getenv("QDRANT_URL")
    vector_database_api_key= os.getenv("QDRANT_API_KEY")

    return vector_database(api_url=vector_database_url, api_key=vector_database_api_key)

def create_embeddor() -> Embeddings:
    return Embeddings()

def create_llm() -> llm_client:
    return llm_client()

