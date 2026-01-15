import datetime
import structlog
from pydantic import BaseModel
import shopify
import requests
from typing import Literal, Protocol
from .product_schema import DraftProduct, DraftResponse, Fields, AllShopifyProducts, ShopifyProductSchema
from .schema import Inventory, Inputs, SkuSearchResponse
from .exceptions import ShopifyError

logger = structlog.get_logger(__name__)
    
class Shop(Protocol):
    """An interface with e-commerce methods """
    def make_a_product_draft(self, product_listing: DraftProduct) -> DraftResponse:
        ...

    def get_products_from_store(self, fields: Fields | None = None) -> list:
        ...

    def fill_inventory(self, inventory_data: Inventory):
        ...
    
    async def search_by_sku(self, sku: int) -> SkuSearchResponse | None:
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
        logger.debug("Initialising Shopify Client...")
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = token
        self.shop_url = shop_url
        self.shop_name = shop_name
        self.graph_url = f"https://{shop_url}/admin/api/2024-01/graphql.json"
        self.locations = locations.create_map()
        self.location_list = locations.locations
        session = shopify.Session(
            shop_url=f"{shop_name}/myshopify.com",
            version="2024-10",
            token=token
        )
        self.client = shopify.ShopifyResource.activate_session(session)
        logger.info("Initialised Client From Concrete")

    def make_a_product_draft(self, product_listing: DraftProduct) -> DraftResponse:
        # could make sure the product doesnt already exist, not sure how it works because it needs to be shopify product id rather than the SKU
        # potentially could just make the draft and then on review in shopifys Ui it'll say a product with that SKU already exists
        logger.debug("Started make_a_product_draft", draft_product=product_listing.model_dump_json())
        product_listing.validate_length()

        # Create blank canvas shopify product
        product = shopify.Product()

        product.title = product_listing.title.title()
        product.body_html = product_listing.description
        product.product_type = product_listing.type.title()
        product.vendor = product_listing.vendor.title()
        product.tags = product_listing.tags
        product.status = "draft"

        # pydantic model need to serialise it explicitly
        options = product_listing.options
        product.options = options

        variants = []
        for variant_listing in product_listing.variants:
            variant = shopify.Variant()

            variant.option1 = variant_listing.option1_value.option_value

            if len(options) > 1 and variant_listing.option2_value:
                variant.option2 = variant_listing.option2_value.option_value
            
            if len(options) > 2 and variant_listing.option3_value:
                variant.option3 = variant_listing.option3_value.option_value
            
            variant.price = str(variant_listing.price)
            variant.sku = variant_listing.sku
            variant.barcode = variant_listing.barcode
            if variant_listing.compare_at:
                # name query what its actually called in the api
                variant.compare_at_price = str(variant_listing.compare_at)
            
            variant.weight = variant_listing.product_weight
            variant.weight_unit = "kg"

            variant.inventory_management = "shopify"
            
            variants.append(variant)
        
        product.variants = variants
        success = product.save()
        if not success:
            logger.error("Failed to create product", product_listing_title=product_listing.title, error=product.errors.full_messages())
            # print(f"\n\nDir on errors method: {dir(product.errors)}")
            raise ShopifyError("Failed to save draft product")

        logger.debug("Saved product to shopify")

        product.reload()
        logger.debug("Reload product to get shopify internal generated data")

        # have to wait until its saved in the database
        # it generates an inventory item id when saved not when local
        inventory_item_ids = []
        for idx, variant in enumerate(product.variants):
            varaiants_inventory_wanted = product_listing.variants[idx].inventory_at_stores
            if varaiants_inventory_wanted is None:
                continue
            # may have to design the inventory model to be able to be None on the stores in case of more stores added
            inventory_model = Inventory(
                inventory_item_id = str(variant.inventory_item_id),

                stores = [
                    Inputs(
                        name_of_store="City",
                        inventory_number=varaiants_inventory_wanted.city
                    ),
                    Inputs(
                        name_of_store="South Melbourne",
                        inventory_number=varaiants_inventory_wanted.south_melbourne
                    )
                ]
            )
            inventory_item_ids.append(inventory_model)

        logger.debug("Retrieved inventory_item_ids", inventory_item_ids=inventory_item_ids, length=len(inventory_item_ids))

        idx = product.id
        return DraftResponse(
            title = product_listing.title,
            id = str(idx),
            variant_inventory_item_ids=inventory_item_ids,
            url = f"https://admin.shopify.com/store/{self.shop_name}/products/{idx}",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
        )

    def make_available_at_all_locations(self, inventory_item_id: str):
        """Function to make a product available at every store"""
        logger.debug("Starting make_available_at_all_locations", inventory_item_id=inventory_item_id)

        mutation = """
mutation InventoryActivateAtLocation($inventoryItemId: ID!, $locationId: ID!) {
  inventoryActivate(
    inventoryItemId: $inventoryItemId
    locationId: $locationId
  ) {
    inventoryLevel {
      id
      location {
        id
        name
      }
      item {
        id
      }
    }
    userErrors {
      field
      message
    }
  }
}
        """

        inventory_item_id = f"gid://shopify/InventoryItem/{inventory_item_id}" if "gid://shopify/InventoryItem/" not in inventory_item_id else inventory_item_id

        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        for location in self.location_list:
            variables = {
                "inventoryItemId": inventory_item_id,
                "locationId": location.id,
            }

            response = requests.post(url=self.graph_url, headers=headers, json={"query": mutation, "variables": variables})
            if response.status_code != 200:
                logger.error("incorrect status code %s", response.status_code)
                return False

            response_dict = response.json()
            errors = response_dict.get("errors", None)
            if errors:
                logger.error("Errors: %s", errors)
                return False

            logger.debug("Response Returned", response=response.json())

        logger.info("Complete item assignment to all stores", inventory_item_id=inventory_item_id)
        return True

    def fill_inventory(self, inventory_data: Inventory) -> bool:
        """Hitting the inventory api"""
        logger.debug("Starting inventory service for request - product_id: %s, stores_changing: %s", inventory_data.inventory_item_id, [stores.name_of_store for stores in inventory_data.stores])

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

        made_available_at_all = self.make_available_at_all_locations(inventory_item_id=inventory_data.inventory_item_id)
        if not made_available_at_all:
            return

        logger.debug("Result Of Making Stores Available: %s", made_available_at_all)
        
        for inventory in inventory_data.stores:
            # Get the actual location ID from the location name (self.locations is already a dict
            location_id = self.locations.get(inventory.name_of_store)
            if not location_id:
                raise ShopifyError(f"Location '{inventory.name_of_store}' not found in locations map")
            
            # Ensure product_id and location_id are in GID format
            inventory_item_gid = inventory_data.inventory_item_id if inventory_data.inventory_item_id.startswith("gid://") else f"gid://shopify/InventoryItem/{inventory_data.inventory_item_id}"
            location_gid = location_id if location_id.startswith("gid://") else f"gid://shopify/Location/{location_id}"
            
            variables = {
                "input": {
                    "reason": "received",
                    "name": "available",
                    "ignoreCompareQuantity": True,
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
                logger.error("Response for store %s - Status Code: %s, Body: %s", inventory.name_of_store, response.status_code, response.json(), exc_info=True)
                raise ShopifyError(f"Bad inventory request status_code {response.status_code}")

            #print(dir(response))
            #print(f"\n\nResponse Content: {response.content}\n\n")
            response_dict = response.json() 
            logger.debug("Response Of Query At Location", location=inventory.name_of_store, response=response_dict)
            
            # Check for GraphQL errors
            errors = response_dict.get("errors", None)  
            if errors:
                logger.error("GraphQL errors for store %s: %s", inventory.name_of_store, errors, exc_info=True)
                raise ShopifyError(f"GraphQL errors: {errors}")
            
            data = response_dict.get("data", {})
            inventory_set_result = data.get("inventorySetQuantities", {})
            logger.debug("Set Inventory", inventory_set_result=inventory_set_result, name_of_store=inventory.name_of_store)
            user_errors = inventory_set_result.get("userErrors", [])
            if user_errors:
                logger.error("User errors for store %s: %s", inventory.name_of_store, user_errors, exc_info=True)
                raise ShopifyError(f"User errors: {user_errors}")
                
            logger.info("Completed request for store: %s, request_data: %s", inventory.name_of_store, response_dict)

        return True

    def get_products_from_store(self, fields: Fields | None = None) -> list:
        """Get all the products from a store with specific tags"""
        try:
            all_products_resource = []

            logger.debug("Sending with fields", fields=fields)
            if fields is not None:
                fields_string = fields.shopify_transform_fields()
                products = shopify.Product.find(limit=250, fields=fields_string)
            else :
                products = shopify.Product.find(limit=250)

            if not products:
                logger.error("Products is None", exc_info=True)
                return None

            while products:
                all_products_resource.extend(products)

                if products.has_next_page():
                    products = products.next_page()
                else:
                    break

            logger.info("Successfully got all the products", length_product=len(all_products_resource))
            return [ShopifyProductSchema.from_shopify_resource(product) for product in all_products_resource]

        except Exception as e:
            logger.error("failed to get shopify products", error=e, exc_info=True)
            return None

    async def search_by_sku(self, sku: int) -> SkuSearchResponse | None:
        """Function that enables sku searching in your shop"""
        logger.debug("Starting search_by_sku", sku=sku)
        query = """
query SearchVariantBySku($q: String!) {
    productVariants(first: 1, query: $q) {
        edges {
            node {
                id
                title
                sku
                price
                product {
                    id
                    title
                }
            }
        }
    }
}
        """

        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        variables = {
            "q": f'sku:"{sku}"'
        }

        response = requests.post(
            url=self.graph_url,
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=30
        )

        if response.status_code != 200:
            logger.error("Failed to search by SKU", sku=sku, status_code=response.status_code)
            return None

        response_dict = response.json()
        logger.debug("Response from search_by_sku", response=response_dict)

        errors = response_dict.get("errors", None)
        if errors:
            logger.error("GraphQL errors in search_by_sku", sku=sku, errors=errors)
            return None

        edges = response_dict.get("data", {}).get("productVariants", {}).get("edges", [])
        if not edges:
            logger.debug("No edges returned, product didnt exist")
            return None

        node = edges[0].get("node")
        return SkuSearchResponse(**node) if node else None

    def what_methods_does_a_variant_have(self):
        """Non protocol function to test logic of the ecommerce api"""
        variant = shopify.Variant.find(id_=42685314990177)
        print(variant.inventory_item_id)