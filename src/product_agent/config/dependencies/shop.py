from abc import ABC, abstractmethod
from product_agent.infrastructure.shopify.client import Locations, ShopifyClient

class EcommerceInit(ABC):
    """A class that specifies the methods required"""
    @abstractmethod
    async def build_shop(self):
        """Implement a build"""
        ...

class ShopifyInit(EcommerceInit):
    """Shopify Init"""
    shop_name:      str
    access_token:   str
    graph_url:      str
    locations:      Locations
    async def build_shop(self):
        """Building the shopify shop"""
        return ShopifyClient(
            locations=self.locations,
            access_token=self.access_token,
            shop_name=self.shop_name
        )

class WooCommerceInit(EcommerceInit):
    """WooCommerce Init"""