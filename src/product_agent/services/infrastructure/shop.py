import logging

from product_agent.infrastructure.shopify.client import Shop
from product_agent.infrastructure.shopify.schemas import DraftProduct, DraftResponse

logger = logging.getLogger(__name__)

def shop_svc(draft_product: DraftProduct, shop: Shop) -> DraftResponse:
    # add any business logic that pops up here later
    # log the draft at info level for an overall check what may have gone wrong very quickly in the final result
    logger.info("Sending Draft", draft=draft_product.model_dump_json())
    return shop.make_a_product_draft(product_listing=draft_product)
