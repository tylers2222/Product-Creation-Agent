import datetime
import structlog
from pydantic import BaseModel
import httpx
from typing import Literal, Protocol
from product_agent.models.shopify import DraftProduct, DraftResponse, Fields, AllShopifyProducts, ShopifyProductSchema
from .types import Inventory, Inputs, SkuSearchResponse, Product
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
    name: str
    id: str

class Locations(BaseModel):
    """Model for specific shopify location and code clarity"""
    locations: list[Location]

    def create_map(self) -> dict:
        """Create a map for the locations"""
        result = {}
        for location in self.locations:
            result[location.name] = location.id

        return result

class ShopifyClient:
    """Shopify class and its methods"""
    def __init__(
        self,
        locations: Locations,
        access_token: str,
        shop_name: str,
        api_version: str = "2024-10"
    ):
        """Init the shopify class"""
        logger.debug("Initialising Shopify Client...")
        self.locations = locations
        self.locations_map = locations.create_map()
        self.access_token = access_token
        self.shop_name = shop_name
        self.api_version = api_version
        self.rest_url = f"https://{shop_name}.myshopify.com/admin/api/{api_version}"
        self.graph_url = f"https://{shop_name}.myshopify.com/admin/api/{api_version}/graphql.json"
        self._client = None
        logger.info("Initialised Client From Concrete")

    async def __aenter__(self):
        """Create HTTP client when entering context"""
        logger.debug("Creating HTTP client for shop", shop_name=self.shop_name)
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close HTTP client when exiting context"""
        logger.debug("Closing HTTP client for shop", shop_name=self.shop_name)
        await self._client.aclose()
        return False

    async def make_a_product_draft(self, product_listing: DraftProduct) -> DraftResponse:
        """Create a product draft via Shopify REST API"""
        logger.debug("Started make_a_product_draft", draft_product=product_listing.model_dump_json())
        product_listing.validate_length()

        # Build variants JSON
        variants = []
        options = product_listing.options
        for variant_listing in product_listing.variants:
            variant_data = {
                "option1": variant_listing.option1_value.option_value,
                "price": str(variant_listing.price),
                "sku": variant_listing.sku,
                "barcode": variant_listing.barcode,
                "weight": variant_listing.product_weight,
                "weight_unit": "kg",
                "inventory_management": "shopify"
            }

            if len(options) > 1 and variant_listing.option2_value:
                variant_data["option2"] = variant_listing.option2_value.option_value

            if len(options) > 2 and variant_listing.option3_value:
                variant_data["option3"] = variant_listing.option3_value.option_value

            if variant_listing.compare_at:
                variant_data["compare_at_price"] = str(variant_listing.compare_at)

            variants.append(variant_data)

        # Build product JSON payload
        payload = {
            "product": {
                "title": product_listing.title.title(),
                "body_html": product_listing.description,
                "product_type": product_listing.type.title(),
                "vendor": product_listing.vendor.title(),
                "tags": product_listing.tags,
                "status": "draft",
                "options": options,
                "variants": variants
            }
        }

        # Make REST API call
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        response = await self._client.post(
            f"{self.rest_url}/products.json",
            headers=headers,
            json=payload
        )

        if response.status_code != 201:
            logger.error("Failed to create product", product_listing_title=product_listing.title, status_code=response.status_code, response=response.text)
            raise ShopifyError(f"Failed to save draft product: {response.status_code}")

        logger.debug("Saved product to shopify")

        # Parse response
        response_data = response.json()
        product_data = response_data.get("product", {})
        product_id = product_data.get("id")
        variants_data = product_data.get("variants", [])

        logger.debug("Product created", product_id=product_id)

        # Build inventory item IDs from response
        inventory_item_ids = []
        for idx, variant_data in enumerate(variants_data):
            varaiants_inventory_wanted = product_listing.variants[idx].inventory_at_stores
            if varaiants_inventory_wanted is None:
                continue

            inventory_model = Inventory(
                inventory_item_id = str(variant_data.get("inventory_item_id")),
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

        return DraftResponse(
            title = product_listing.title,
            id = str(product_id),
            variant_inventory_item_ids=inventory_item_ids,
            url = f"https://admin.shopify.com/store/{self.shop_name}/products/{product_id}",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 201,
        )

    async def make_available_at_all_locations(self, inventory_item_id: str):
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

        for location in self.locations.locations:
            variables = {
                "inventoryItemId": inventory_item_id,
                "locationId": location.id,
            }

            response = await self._client.post(url=self.graph_url, headers=headers, json={"query": mutation, "variables": variables})
            if response.status_code != 200:
                logger.error("incorrect status code %s", response.status_code)
                return False

            response_dict = response.json()
            errors = response_dict.get("errors", None)
            if errors:
                logger.error("Errors: %s", errors)
                return False

            logger.debug("Response Returned", response=response_dict)

        logger.info("Complete item assignment to all stores", inventory_item_id=inventory_item_id)
        return True

    async def fill_inventory(self, inventory_data: Inventory) -> bool:
        """Hitting the inventory api"""
        logger.debug("Starting inventory service for request - product_id: %s, stores_changing: %s", inventory_data.inventory_item_id, [stores.name_of_store for stores in inventory_data.stores])

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

        made_available_at_all = await self.make_available_at_all_locations(inventory_item_id=inventory_data.inventory_item_id)
        if not made_available_at_all:
            return

        logger.debug("Result Of Making Stores Available: %s", made_available_at_all)

        for inventory in inventory_data.stores:
            # Get the actual location ID from the location name
            location_id = self.locations_map.get(inventory.name_of_store)
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

            response = await self._client.post(url=self.graph_url, json={"query": mutation, "variables": variables}, headers=headers)
            if response.status_code != 200:
                logger.error("Response for store %s - Status Code: %s, Body: %s", inventory.name_of_store, response.status_code, response.json(), exc_info=True)
                raise ShopifyError(f"Bad inventory request status_code {response.status_code}")

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

    async def get_products_from_store(self, fields: Fields | None = None) -> list:
        """Get all the products from a store with specific tags"""
        try:
            all_products = []

            logger.debug("Sending with fields", fields=fields)

            # Build query parameters
            params = {"limit": 250}
            if fields is not None:
                params["fields"] = fields.shopify_transform_fields()

            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }

            url = f"{self.rest_url}/products.json"

            # Pagination loop
            while url:
                response = await self._client.get(url, headers=headers, params=params if url == f"{self.rest_url}/products.json" else None)

                if response.status_code != 200:
                    logger.error("Failed to get products", status_code=response.status_code, response=response.text)
                    return None

                response_data = response.json()
                products = response_data.get("products", [])

                if not products:
                    break

                all_products.extend(products)

                # Check for next page via Link header
                link_header = response.headers.get("Link", "")
                next_url = None

                if link_header:
                    # Parse Link header for rel="next"
                    links = link_header.split(",")
                    for link in links:
                        if 'rel="next"' in link:
                            # Extract URL from <...>
                            next_url = link.split(";")[0].strip()[1:-1]
                            break

                url = next_url

            logger.info("Successfully got all the products", length_product=len(all_products))
            return [ShopifyProductSchema.from_rest_api(product) for product in all_products]

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

        response = await self._client.post(
            url=self.graph_url,
            headers=headers,
            json={"query": query, "variables": variables}
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

