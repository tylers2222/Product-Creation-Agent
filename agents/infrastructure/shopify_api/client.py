import datetime
import json
import logging
from operator import inv
import traceback
from pydantic import BaseModel
import shopify
from dotenv import load_dotenv
import os
import requests
from typing import Literal, Protocol
from .product_schema import DraftProduct, DraftResponse
from .schema import Inventory
from .exceptions import ShopifyError

# Add parent directory to Python path so we can import utils
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.timer import timer_func

load_dotenv()

logging.basicConfig(level=logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
    
class Shop(Protocol):
    """An interface with e-commerce methods """
    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
        ...

    def get_products_from_store(self):
        ...

    def fill_inventory(self, inventory_data: Inventory):
        ...

class Location(BaseModel):
    """A singular location"""
    name: Literal["City", "South Melbourne"]
    id: str

class Locations(BaseModel):
    """Model for specific shopify location and code clarity"""
    locations: list[Location]

    def create_map(self) -> dict:
        result = {}
        for location in self.locations:
            result[location.name] = location.id

        return result

class ShopifyClient:
    def __init__(self, api_key: str, api_secret: str, token: str, shop_url: str, shop_name: str, locations: Locations):
        print("Initialising Shopify Client From Concrete...")
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = token
        self.shop_url = shop_url
        self.shop_name = shop_name
        self.graph_url = f"https://{shop_url}/admin/api/2024-01/graphql.json"
        self.locations = locations.create_map()
        session = shopify.Session(
            shop_url=f"{shop_name}/myshopify.com",
            version="2024-10",
            token=token
        )
        self.client = shopify.ShopifyResource.activate_session(session)
        print("Initialised Client From Concrete")

    def make_a_product_draft(self, product_listing: DraftProduct) -> DraftResponse:
        # could make sure the product doesnt already exist, not sure how it works because it needs to be shopify product id rather than the SKU
        # potentially could just make the draft and then on review in shopifys Ui it'll say a product with that SKU already exists
        product_listing.validate_length()

        # Create blank canvas shopify product
        product = shopify.Product()

        product.title = product_listing.title
        product.body_html = product_listing.description
        product.product_type = product_listing.type
        product.vendor = product_listing.vendor
        product.tags = product_listing.tags
        product.status = "draft"

        options = product_listing.options
        product.options = options

        variants = []
        for variant_listing in product_listing.variants:
            variant = shopify.Variant()

            variant.option1 = variant_listing.option1_value

            if len(options) > 1 and variant_listing.option2_value:
                variant.option2 = variant_listing.option2_value
            
            if len(options) > 2 and variant_listing.option3_value:
                variant.option3 = variant_listing.option3_value
            
            variant.price = str(variant_listing.price)
            variant.sku = variant_listing.sku
            variant.barcode = variant_listing.barcode
            if variant_listing.compare_at:
                # name query what its actually called in the api
                variant.compare_at_price = str(variant_listing.compare_at)
            
            variant.weight = variant_listing.product_weight
            variant.weight_unit = "kg"
            
            variants.append(variant)
        
        product.variants = variants

        success = product.save()
        if not success:
            logging.error(f"Failed to create {product_listing.title}: {product.errors.full_messages()}")
            # print(f"\n\nDir on errors method: {dir(product.errors)}")
            raise ShopifyError("Failed to save draft product")

        idx = product.id
        return DraftResponse(
            title = product_listing.title,
            id = str(idx),
            url = f"https://admin.shopify.com/store/{self.shop_name}/products/{idx}",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
        )

    def fill_inventory(self, inventory_data: Inventory) -> bool:
        """Hitting the inventory api"""
        logging.info("Starting inventory service for request - product_id: %s, stores_changing: %s", 
                     inventory_data.product_id, 
                     [stores.name_of_store for stores in inventory_data.stores])

        # Mutation to adjust inventory
        mutation = """
mutation InventorySet($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup {
      reason
      changes {
        name
        delta
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""     

        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        for inventory in inventory_data.stores:
            # Get the actual location ID from the location name (self.locations is already a dict)
            location_id = self.locations.get(inventory.name_of_store)
            if not location_id:
                raise ShopifyError(f"Location '{inventory.name_of_store}' not found in locations map")
            
            # Ensure product_id and location_id are in GID format
            inventory_item_gid = inventory_data.product_id if inventory_data.product_id.startswith("gid://") else f"gid://shopify/InventoryItem/{inventory_data.product_id}"
            location_gid = location_id if location_id.startswith("gid://") else f"gid://shopify/Location/{location_id}"
            
            variables = {
                "input": {
                    "reason": "Correction",
                    "name": "Stock Update",
                    "quantities": [
                        {
                            "inventoryItemId": inventory_item_gid,
                            "locationId": location_gid,
                            "quantity": inventory.inventory_number
                        }
                    ]
                }
            }

            response = requests.post(url=self.graph_url, json={"query": mutation, "variables": variables}, headers=headers)
            if response.status_code != 200:
                logging.error("Response for store %s - Status Code: %s, Body: %s", inventory.name_of_store, response.status_code, response.json(), exc_info=True)
                raise ShopifyError(f"Bad inventory request status_code {response.status_code}")

            #print(dir(response))
            #print(f"\n\nResponse Content: {response.content}\n\n")
            response_dict = response.json()  # Parse JSON response to dict
            
            # Check for GraphQL errors
            errors = response_dict.get("errors", None)  
            if errors:
                logging.error("GraphQL errors for store %s: %s", inventory.name_of_store, errors, exc_info=True)
                raise ShopifyError(f"GraphQL errors: {errors}")
            
            data = response_dict.get("data", {})
            inventory_set_result = data.get("inventorySetQuantities", {})
            user_errors = inventory_set_result.get("userErrors", [])
            if user_errors:
                logging.error("User errors for store %s: %s", inventory.name_of_store, user_errors, exc_info=True)
                raise ShopifyError(f"User errors: {user_errors}")
                

            logging.info("Completed request for store: %s, request_data: %s", inventory.name_of_store, response_dict)

        return True

    def get_products_from_store(self):
        try:
            all_products = []
            products = shopify.Product.find(limit=250, fields="id,title,body_html,product_type,tags")
            if not products:
                logging.error("Products is None")
                return None

            while products:
                all_products.extend(products)

                if products.has_next_page():
                    products = products.next_page()
                else:
                    break

            logging.info(f"Successfully got all the products -> Length = {len(all_products)}")
            return all_products

        except Exception as e:
            logging.error(f"failed to get shopify products: {e}")
            print(traceback.format_exc())
            return None
