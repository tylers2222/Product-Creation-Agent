import json
import logging
import os
import sys
from dotenv import load_dotenv
from datetime import date

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.infrastructure.vector_database.db import vector_database, VectorDb
from agents.infrastructure.vector_database.embeddings import Embeddor, Embeddings
from agents.infrastructure.shopify_api.client import ShopifyClient, Shop
from agents.infrastructure.shopify_api.product_schema import Fields
from services.internal.vector_db import batch_products_to_vector_db
from config import create_vector_database, create_embeddor, create_shop

logger = logging.getLogger(__name__)

class ShopifyProductAndVectorTool:
    """
    A tool to help the codebase manage some real collection population
    Also sends a whole store to json in versions for testing later down the line
    """
    def __init__(self, db: VectorDb, embeddor: Embeddor, shop: Shop):
        self.vector_db = db
        self.embeddor = embeddor
        self.shop = shop

    def _send_to_file(self, data: dict):
        """Send the data to a json file"""
        version_number = 0
        path_name = f"store_data_v{version_number}.json"
        version_already_exists = os.path.exists(f"../store_data/{path_name}")
        if version_already_exists:
            raise ValueError(f"That version {version_number} of the store already exists")

        with open(f"../store_data/{path_name}", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=3, default=str)

        print(f"Succesfully written to file: {path_name}, Version: {version_number}")

    def get_products_send_to_file(self):
        """Get products and send to json file only"""
        fields = Fields(
            id=True,
            title=True,
            body_html=True,
            category=True,
            vendor=True,
            product_type=True,
            collections=True,
            tags=True,
            status=True
        )

        products = self.shop.get_products_from_store(fields=fields)
        if not products:
            return

        # workout in multi tennant, passing an id to log whichs tennant is undergoing this process
        print(dir(products[0]))
        logging.info("Successfully Finished Obtaining Products", length_of_products_in_store=len(products))

        data_for_file = {
            "date": str(date.today()),
            "store_data": [product.to_dict() for product in products]
        }

        self._send_to_file(data=data_for_file)

    def get_products_send_to_vector_db(self):
        fields = Fields(
            id=True,
            title=True,
            body_html=True,
            category=True,
            vendor=True,
            product_type=True,
            collections=True,
            tags=True,
            status=True
        )

        products = self.shop.get_products_from_store(fields=fields)
        if not products:
            return

        sent = batch_products_to_vector_db(products=products, 
            database=self.vector_db, 
            embedder=self.embeddor, 
            collection_name="shopify_products-latest")
        if sent is None:
            raise ValueError("Sent to vector db didnt return a success")

        print("Sucessfully sent to vector_database")

    def get_products_send_to_file_and_vectordb(self):
        # Can add Fields from our internal schema into here
        fields = Fields(
            id=True,
            title=True,
            body_html=True,
            category=True,
            vendor=True,
            product_type=True,
            collections=True,
            tags=True,
            status=True
        )

        products = self.shop.get_products_from_store(fields=fields)
        if not products:
            return

        # workout in multi tennant, passing an id to log whichs tennant is undergoing this process
        logging.info("Successfully Finished Obtaining Products", length_of_products_in_store=len(products))

        data_for_file = {
            "date": str(date.today()),
            "store_data": products
        }

        self._send_to_file(data=data_for_file)

        # get collection_name from env or redis
        sent = batch_products_to_vector_db(products=products, 
            database=self.vector_db, 
            embedder=self.embeddor, 
            collection_name="shopify_products-latest")
        if sent is None:
            raise ValueError("Sent to vector db didnt return a success")

        print("Sucessfully sent to vector_database")

if __name__ == "__main__":
    vector_db_impl = create_vector_database()
    embeddor_impl = create_embeddor()
    shop_impl = create_shop()
    t = ShopifyProductAndVectorTool(vector_db_impl, embeddor_impl, shop_impl)
    #t.get_products_send_to_file()
    #t.get_products_send_to_file_and_vectordb()
    t.get_products_send_to_vector_db()