import datetime
import logging
import trace
import traceback
import shopify
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Protocol
from .product_schema import DraftProduct, DraftResponse, Variant
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

api_key = os.getenv("SHOPIFY_API_KEY")
api_secret = os.getenv("SHOPIFY_API_SECRET")
token = os.getenv("SHOPIFY_TOKEN")
shop_name = "evelynfaye"

session = shopify.Session(
    shop_url=f"{shop_name}/myshopify.com",
    version="2024-10",
    token=token
)
    
class Shop(Protocol):
    """An interface with e-commerce methods """
    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
        ...

    def get_products_from_store(self):
        ...

class ShopifyClient:
    def __init__(self):
        print("Initialising Shopify Client From Concrete...")
        self.client = shopify.ShopifyResource.activate_session(session)
        print("Initialised Client From Concrete")

    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
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
            url = f"https://admin.shopify.com/store/{shop_name}/products/{idx}",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
        )

    @timer_func
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