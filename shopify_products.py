import logging
import shopify
from agents.infrastructure.vector_database.db import vector_database, vector_db
from agents.infrastructure.vector_database.embeddings import Embeddor, Embeddings
from agents.agent.services import add_products_to_vector_db
from agents.infrastructure.shopify_api.client import ShopifyClient, Shop

def send_products_to_vector_database():
    """A function manually run in staging to populate the vector database with shopify products"""

    print("="*60) 
    print("STARTING THE SEND OF SHOPIFY PRODUCTS TO VECTOR DATABASE") 

    db: vector_db = vector_database()
    embeddor: Embeddor = Embeddings()
    shop: Shop = ShopifyClient()

    products = shop.get_products_from_store()
    if not products:
        return

    logging.info("Successfully Finished Obtaining Products")

    db_resp = add_products_to_vector_db(products, database=db, embedder=embeddor, collection_name="shopify_products")
    if not db_resp:
        return

    print()
    logging.info(db_resp)
    print()

    print("="*60) 

if __name__ == "__main__":
    send_products_to_vector_database()