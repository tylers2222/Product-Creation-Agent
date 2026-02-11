import inspect
import structlog
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from product_agent.config import ServiceContainer

from product_agent.services.infrastructure.image_scraper import image_scraper_svc, image_to_bytes_svc

logger = structlog.getLogger(__name__)

class ImageScrape(TypedDict):
    """Image Scraper Workflow"""
    query:                  str # Query the user asked
    variants:               list # The variants they asked for
    num_images:             int = 5 # Number of images to return if finding them manually
    urls:                   list[str] # Urls to collect image bytes from
    image_bytes:            dict # Holds url as the key and the bytes as the value
    # Return the url that the image comes from
    # This can map to the correct bytes in the dictionary
    classification:         str


class ImageScrapeWorkflow:
    """
    A workflow that defines the nodes undertaken during an image scrape

    This may check a cache in the future for the query
    """

    def __init__(self, sc: ServiceContainer):
        self.sc = sc

        workflow = StateGraph(ImageScrape)
        # add nodes 
        workflow.add_conditional_edges(START, self.routing_function, {
            "urls": "get_images_as_bytes",
            "no_urls": "get_images"
        })

        workflow.compile()

    def routing_function(self, state: ImageScrape):
        """Routing the start of the image workflow"""
        if state["urls"]:
            # URLs already exist we can just use those
            return "urls"
        return "no_urls"

    async def get_images(self, state: ImageScrape):
        """Scraping image links in the workflow layer"""
        logger.debug("Starting %s", inspect.stack()[0][3])

        query = state["query"]
        num_images = state["num_images"]
        logger.debug("Starting image scrape node with query", query=query, num_images=num_images)
        scraped_image_urls = await image_scraper_svc(
            image_scraper=self.sc.image_scraper,
            query=query,
            num_images=num_images
        )

        return {
            "urls": scraped_image_urls
        }

    async def get_images_as_bytes(self, state: ImageScrape):
        """
        Turn the image into usable bytes
        Most LLM API's expect the base64 encoded version
        """
        logger.debug("Starting %s", inspect.stack()[0][3])

        urls = state["urls"]
        images_as_base64 = await image_to_bytes_svc(image_urls=urls)
        logger.debug("Returned images as base64", length=len(images_as_base64))

        return {
            "image_bytes": images_as_base64
        }

    async def image_classification(self, state: ImageScrape):
        """
        Possible routes:
            On specific subs or settings you can change it

            Route 1:
                HITL choose which image to use for that product

            Route 2:
                Gemini based classification (higher subs only)
        """
        node_key = "image_classification"
        logger.debug(
            "Starting node %s", inspect.stack()[0][3],
            node_key=node_key
        )

        
