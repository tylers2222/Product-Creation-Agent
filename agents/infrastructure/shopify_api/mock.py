import datetime
import structlog
from agents.infrastructure.shopify_api.product_schema import DraftResponse, DraftProduct
from agents.infrastructure.shopify_api.exceptions import ShopifyError

logger = structlog.getLogger(__name__)

class MockShop:
    def __init__(self) -> None:
        pass

    def make_a_product_draft(self, shop_name: str, product_listing: DraftProduct) -> DraftResponse:
        logger.debug("Called: MockShop.make_a_product")
        if len(product_listing.variants) == 0:
            raise ShopifyError("No proposed variants")

        logger.debug("MockShop.make_a_product returned DraftResponse")
        return DraftResponse(
            title = product_listing.title,
            url = f"https://admin.shopify.com/store/{shop_name}/products/5327895723",
            time_of_comepletion = datetime.datetime.now(),
            status_code = 200,
        )