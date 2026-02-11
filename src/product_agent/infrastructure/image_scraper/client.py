"""
Simple Google Images URL scraper
Returns first K image URLs for a given search query
"""
import inspect
import requests
import structlog

from typing import Protocol
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

logger = structlog.getLogger(__name__)

class ImageScraper(Protocol):
    """Protocol defining an image scraper"""
    async def get_google_images(
        self,
        query: str,
        num_images: int = 5,
        headless: bool = True
    ) -> list[str]:
        """Protocol method for an image scraper"""
        ...

class ImageScraperSelenium:
    """
    Image Scraper using selenium
    """
    def __init__(self, driver_path: str):
        self.driver_path = driver_path

    def _create_driver(self, headless: bool):
        logger.debug("Starting %s", inspect.stack()[0][3])
        service = Service(executable_path=self.driver_path)
        if headless:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            return webdriver.Chrome(options=chrome_options, service=service)

        return webdriver.Chrome(service=service)

    async def get_google_images(self, query: str, num_images: int = 5, headless: bool = True) -> list[str]:
        """Get google images using the browser"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        driver = self._create_driver(headless=headless)

        try:
            # Navigate to Google Images
            search_url = f"https://www.google.com/search?tbm=isch&q={query}"
            logger.debug("Starting image scraper for URL", url=search_url)
            driver.get(search_url)
            time.sleep(2)

            # Find all thumbnail images (includes data:image base64 thumbnails)
            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

            if not thumbnails:
                logger.warning("No thumbnails found", query=query)
                return []

            logger.debug("Found thumbnails", count=len(thumbnails), query=query)

            image_urls = []
            seen_urls = set()  # Track unique URLs
            thumbnail_index = 0
            max_attempts = min(num_images * 3, len(thumbnails))  # Try up to 3x to handle issues

            while len(image_urls) < num_images and thumbnail_index < max_attempts:
                i = thumbnail_index
                thumbnail_index += 1

                try:
                    # Scroll thumbnail into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thumbnails[i])
                    time.sleep(0.3)

                    # Use JavaScript click to open preview panel (stays on Google Images)
                    driver.execute_script("arguments[0].click();", thumbnails[i])
                    time.sleep(1)  # Wait for preview panel to load

                    # Find preview panel container
                    preview_containers = [
                        '.v6bUne',  # Main preview container
                        '.p7sI2',   # Alternative container
                    ]

                    url_found = False
                    for container_selector in preview_containers:
                        try:
                            containers = driver.find_elements(By.CSS_SELECTOR, container_selector)
                            for container in containers:
                                # Look for large image inside this container
                                try:
                                    # Find img with class sFlh5c inside the container
                                    img = container.find_element(By.CSS_SELECTOR, 'img.sFlh5c')
                                    src = img.get_attribute('src')

                                    # Must be real HTTP URL (not base64, not Google assets, not duplicate)
                                    if (src and
                                        src.startswith('http') and
                                        'data:image' not in src and
                                        'gstatic.com' not in src and
                                        'google.com/logos' not in src and
                                        'encrypted-tbn' not in src and  # Skip encrypted thumbnails
                                        src not in seen_urls):

                                        seen_urls.add(src)
                                        image_urls.append(src)
                                        logger.debug("Image URL extracted", index=i+1, url=src[:80], total_collected=len(image_urls))
                                        url_found = True
                                        break
                                except:
                                    continue

                            if url_found:
                                break
                        except:
                            continue

                    if not url_found:
                        logger.debug("No image URL found in preview", index=i+1)

                except Exception as e:
                    logger.debug("Error processing thumbnail", index=i+1, error=str(e)[:50])
                    continue

            logger.info("Image scraping completed", query=query, images_collected=len(image_urls), requested=num_images)
            return image_urls

        finally:
            driver.quit()