import asyncio
import json
import os
import random
import sys
import traceback
import uuid

from dotenv import load_dotenv

# Add parent directory to Python path so we can import packages
# Go up from agent -> agents -> Product generating agent (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(agents_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.infrastructure.vector_database.embeddings_test import MockEmbeddor
from agents.infrastructure.vector_database.db_test import MockVectorDb
from agents.infrastructure.firecrawl_api.client_test import MockScraperClient
from agents.infrastructure.shopify_api.client_test import MockShop

from agents.agent.agent import ShopifyProductWorkflow
from agents.agent.llm_test import MockLLM

from agents.infrastructure.vector_database.embeddings import Embeddings
from agents.infrastructure.vector_database.db import vector_database
from agents.infrastructure.firecrawl_api.client import FirecrawlClient
from agents.infrastructure.shopify_api.client import ShopifyClient
from agents.infrastructure.shopify_api.product_schema import InventoryAtStores, Option, Variant
from agents.agent.llm import llm_client

from agents.agent.prompts import format_product_input, PromptVariant
from agents.agent.tools import create_all_tools, ServiceContainer


from config import create_service_container

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "shopify-product-workflow"

product_name = "Oxyshred Protein Lean Bar"
brand = "EHP"
option_1_1 = Option(option_name="Size", option_value="50 g")
option_1_2 = Option(option_name="Size", option_value="Box of 12")
option_2_1 = Option(option_name="Flavour", option_value="White Choc Caramel")
option_2_2 = Option(option_name="Flavour", option_value="Strawberries & Cream")
option_2_3 = Option(option_name="Flavour", option_value="Choc Peanut Caramel")
option_2_4 = Option(option_name="Flavour", option_value="Cookies & Cream")
variants = [
    # 50g variants
    Variant(option1_value=option_1_1, option2_value=option_2_1, sku=922026, barcode="0810095637971", price=4.95, product_weight=0.05, inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)),
    Variant(option1_value=option_1_1, option2_value=option_2_2, sku=922028, barcode="0810095637933", price=4.95, product_weight=0.05, inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)),
    Variant(option1_value=option_1_1, option2_value=option_2_3, sku=922027, barcode="0810095637988", price=4.95, product_weight=0.05, inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)),
    Variant(option1_value=option_1_1, option2_value=option_2_4, sku=922029, barcode="0810095637945", price=4.95, product_weight=0.05, inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)),
]
pv = PromptVariant(
    brand_name=brand,
    product_name=product_name,
    variants=variants
)

request_id = uuid.UUID()

class unittest:
    def __init__(self) -> None:
        self.scraper = MockScraperClient()
        self.embeddor = MockEmbeddor()
        self.vector_db = MockVectorDb()
        self.shop = MockShop()
        self.llm = MockLLM()

    def test_1(self):
        print("="*60)
        print("STARTING unittest.test_1")
        s = ShopifyProductWorkflow(shop=self.shop, scraper=self.scraper, vector_db=self.vector_db, embeddor=self.embeddor, llm=self.llm)

        try:
            product_name = "Freak3d"
            brand = " Anabolix Nutrition"
            option = Option(option_name="Size", option_value="1 kg")
            variants = [Variant(option_1=option, sku=random.randint(99999, 999999), barcode=random.randint(999999999999,9999999999999), price=49.95)]
            pv = PromptVariant(
                brand_name=brand,
                product_name=product_name,
                variants=variants
            )

            format_product_input(prompt_variant=pv)
            s.service_workflow(query="Hi", request_id=str(request_id))

        except Exception as e:
            print(f"Error: {e}")

            print(traceback.format_exc())
        print("Completed unittest.test_1")

class integrationtests:
    def __init__(self):
        self.sc = create_service_container()
        self.tools = create_all_tools(self.sc)
        self.workflow = ShopifyProductWorkflow(shop=self.sc.shop, scraper=self.sc.scraper, vector_db=self.sc.vector_db, embeddor=self.sc.embeddor, llm=self.sc.llm, tools=self.tools)

    async def test_shopify_workflow(self):
        try:
            query = format_product_input(prompt_variant=pv)
            await self.workflow.service_workflow(query=query, request_id=str(request_id))

        except Exception as e:
            print(f"Error: {e} -> Traceback: \n{traceback.format_exc()}")

    def test_node_one(self):
        query = format_product_input(prompt_variant=pv)
        test_state = {
            "query": query
        }

        # debugging added model 
        assert "Inventory: city=" in query or "inventory" in query.lower()
        print("Query: ", query)

        result = self.workflow.query_extract(state=test_state)
        result_as_string = json.dumps(result)
        assert "'inventory_at_stores': {'city': 15, 'south_melbourne': 15" in result_as_string

        print(result)

if __name__ == "__main__":
    #ut = unittest()
    #ut.test_1()

    it = integrationtests()
    asyncio.run(it.test_shopify_workflow())
    #it.test_node_one()