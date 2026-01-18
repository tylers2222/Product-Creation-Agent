"""
Service Container - Holds all infrastructure dependencies.

This module defines the ServiceContainer dataclass and factory functions
to build containers with real or mock implementations.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

from product_agent.infrastructure.firecrawl.client import FirecrawlClient, Scraper
from product_agent.infrastructure.shopify.client import ShopifyClient, Shop, Locations, Location
from product_agent.infrastructure.vector_db.client import vector_database, VectorDb
from product_agent.infrastructure.vector_db.embeddings import Embeddings, Embeddor
from product_agent.infrastructure.llm.client import open_ai_client, LLM

load_dotenv()


@dataclass
class ServiceContainer:
    """
    Container holding all infrastructure dependencies.

    This is the central dependency injection container. All services and agents
    receive their dependencies through this container rather than constructing
    them directly.
    """
    shop: Shop
    scraper: Scraper
    vector_db: VectorDb
    embeddor: Embeddor
    llm: LLM


def _get_required_env(key: str) -> str:
    """Get required environment variable or raise clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set")
    return value


def build_service_container() -> ServiceContainer:
    """
    Build a ServiceContainer with real production implementations.

    Raises:
        EnvironmentError: If required environment variables are missing.
    """
    locations = Locations(
        locations=[
            Location(name="City", id=f"gid://shopify/Location/{_get_required_env('LOCATION_ONE_ID')}"),
            Location(name="South Melbourne", id=f"gid://shopify/Location/{_get_required_env('LOCATION_TWO_ID')}")
        ]
    )

    shop = ShopifyClient(
        api_key=_get_required_env("SHOPIFY_API_KEY"),
        api_secret=_get_required_env("SHOPIFY_API_SECRET"),
        token=_get_required_env("SHOPIFY_TOKEN"),
        shop_name=_get_required_env("SHOP_NAME"),
        shop_url=_get_required_env("SHOP_URL"),
        locations=locations
    )

    scraper = FirecrawlClient(api_key=_get_required_env("FIRECRAWL_API_KEY"))
    vector_db = vector_database(
        api_url=_get_required_env("QDRANT_URL"),
        api_key=_get_required_env("QDRANT_API_KEY")
    )
    embeddor = Embeddings()
    llm = open_ai_client()

    return ServiceContainer(
        shop=shop,
        scraper=scraper,
        vector_db=vector_db,
        embeddor=embeddor,
        llm=llm
    )


def build_mock_service_container() -> ServiceContainer:
    """Build a ServiceContainer with mock implementations for testing."""
    # Import mocks at runtime to avoid circular imports and keep tests separate
    from tests.mocks.shopify_mock import MockShop
    from tests.mocks.firecrawl_mock import MockScraperClient
    from tests.mocks.vector_db_mock import MockVectorDb
    from tests.mocks.embeddings_mock import MockEmbeddor
    from tests.mocks.llm_mock import MockLLM

    return ServiceContainer(
        shop=MockShop(),
        scraper=MockScraperClient(),
        vector_db=MockVectorDb(),
        embeddor=MockEmbeddor(),
        llm=MockLLM()
    )
