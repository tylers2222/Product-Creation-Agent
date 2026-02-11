"""
Service Container - Holds all infrastructure dependencies.

This module defines the ServiceContainer dataclass and factory functions
to build containers with real or mock implementations.
"""
import os
from dataclasses import dataclass
from typing import Dict
from pydantic import BaseModel
import structlog
import yaml
from dotenv import load_dotenv
from unittest.mock import Mock

from product_agent.config.dependencies.shop import EcommerceInit
from product_agent.infrastructure.firecrawl.client import FirecrawlClient, Scraper
from product_agent.infrastructure.shopify.client import ShopifyClient, Shop, Locations, Location
from product_agent.infrastructure.vector_db.client import vector_database, VectorDb
from product_agent.infrastructure.vector_db.embeddings import Embeddings, Embeddor
from product_agent.infrastructure.llm.client import LLM, OpenAiClient, GeminiClient
from product_agent.infrastructure.image_scraper.client import ImageScraper, ImageScraperSelenium

load_dotenv()

logger = structlog.getLogger(__name__)

@dataclass
class ServiceContainer:
    """
    Container holding all infrastructure dependencies.

    This is the central dependency injection container. All services and agents
    receive their dependencies through this container rather than constructing
    them directly.
    """
    shop:               Shop
    scraper:            Scraper
    vector_db:          VectorDb
    embeddor:           Embeddor
    llm:                Dict[str, Dict | None]
    image_scraper:      ImageScraper

    def llm_config(self, node_key):
        """Pass a key for the service, get the client and model"""
        class LLMConfig(BaseModel):
            """Return model"""
            client: LLM
            model: str

        model = self.llm["models"][node_key]["primary"]
        client = None
        if "gemini" in model:
            client = self.llm["clients"]["gemini"]

        if "gpt" in model:
            client = self.llm["clients"]["gemini"]

        if "claude" in model:
            client = self.llm["clients"]["anthropic"]

        logger.info(
            "Called for llm client and model",
            model=model,
            client=client
        )

        return LLMConfig(
            client=client,
            model=model
        )

def _get_required_env(key: str) -> str:
    """Get required environment variable or raise clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set")
    return value

class RealServiceContainer:
    def __init__(self):
        # Check max conn pool later
        self._vector_db_conn = None
        if self._vector_db_conn is None:
            self._vector_db_conn = vector_database(
                api_url=_get_required_env("QDRANT_URL"),
                api_key=_get_required_env("QDRANT_API_KEY")
            )

    async def build_service_container(
        self,
        shop: EcommerceInit,
        scraper_key: str,
        embeddor_key: str,
        gemini_llm: LLM,
        open_ai_llm: LLM,
        image_scraper: ImageScraper,
        subscription: str,
        tenant_id: str
    ):
        """Build a requests service container"""
        shop_built = shop.build_shop()
        scraper = FirecrawlClient(api_key=scraper_key)
        vector_db = self._vector_db_conn
        embeddor = Embeddings(
            api_key=embeddor_key,
        )

        llm =  {
            "clients": {
                "gemini": gemini_llm,
                "open_ai": open_ai_llm,
            },
            "models": None
        }
        with open(
            "product_agent.config.files.llm_provider.yaml",
            "r",
            encoding="utf-8"
        ) as config:
            models = yaml.safe_load(config)
            llm["models"] = models["llm_factory"]["subscriptions"][subscription]["processes"]

        logger.info(
            "Built service container for client",
            tenant_id=tenant_id,
            subscription=subscription,
            shop=shop_built.shop_domain,
            scraper=type(scraper).__name__,
            vector_db_status=vector_db.status,
            clients=llm["clients"].keys(),
            available_processes=llm["models"].keys(),
        )

        return ServiceContainer(
            shop=shop_built,
            scraper=scraper,
            vector_db=vector_db,
            embeddor=embeddor,
            llm=llm,
            image_scraper=image_scraper
        )


def local_build_service_container() -> ServiceContainer:
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
        locations=locations,
        access_token=_get_required_env("SHOPIFY_TOKEN"),
        shop_name=_get_required_env("SHOP_NAME"),
        api_version="2024-10"
    )

    scraper = FirecrawlClient(api_key=_get_required_env("FIRECRAWL_API_KEY"))
    vector_db = vector_database(
        api_url=_get_required_env("QDRANT_URL"),
        api_key=_get_required_env("QDRANT_API_KEY")
    )
    embeddor = Embeddings(_get_required_env("OPENAI_API_KEY"))
    llm = {
        "open_ai": OpenAiClient(api_key=_get_required_env("OPENAI_API_KEY")),
        "gemini": GeminiClient(api_key=_get_required_env("GEMINI_API_KEY"))
    }
    image_scraper = ImageScraperSelenium(_get_required_env("DRIVER_PATH"))

    return ServiceContainer(
        shop=shop,
        scraper=scraper,
        vector_db=vector_db,
        embeddor=embeddor,
        llm=llm,
        image_scraper=image_scraper
    )

# Alias for backwards compatibility
build_service_container = local_build_service_container

def build_mock_service_container() -> ServiceContainer:
    """
    Build a ServiceContainer with mock implementations for testing.

    Returns:
        ServiceContainer: Container with mocked dependencies.
    """

    return ServiceContainer(
        shop=Mock(spec=Shop),
        # Used the concrete because protocol is duck typed
        # Many interfaces can be satisfied with one concrete
        # Using Mock Spec it wasnt designed for that
        # If scraper methods change the urls part will be got antoher way
        # Therefore it had to be a seperate protocol but now its satisfied
        # by the same client
        scraper=Mock(spec=FirecrawlClient),
        vector_db=Mock(spec=VectorDb),
        embeddor=Mock(spec=Embeddor),
        llm={"open_ai": Mock(spec=LLM), "gemini": Mock(spec=LLM)},
        image_scraper=Mock(spec=ImageScraper)
    )
