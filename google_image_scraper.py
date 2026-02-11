"""
Simple Google Images URL scraper
Returns first K image URLs for a given search query
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import json
import re

DRIVER_PATH = "/Users/tylerstewart/Downloads/chromedriver-mac-arm64-2/chromedriver"


def get_google_image_urls(query: str, num_images: int = 10) -> list:
    """
    Get the first K image URLs from Google Images for a search query.

    Args:
        query: Search term (e.g., "chicken")
        num_images: Number of image URLs to return (default 10)

    Returns:
        List of image URLs (HTTP links)
    """
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    try:
        # Navigate to Google Images
        search_url = f"https://www.google.com/search?tbm=isch&q={query}"
        driver.get(search_url)
        time.sleep(2)

        # Get page source and extract image URLs using regex
        # Google stores actual image URLs in the page's JavaScript
        page_source = driver.page_source

        # Pattern to find actual image URLs in Google's data
        # They're usually in format: ["url","actual-image-url.jpg"
        pattern = r'"(https://[^"]+\.(?:jpg|jpeg|png|gif|webp))"'
        matches = re.findall(pattern, page_source)

        # Filter out Google's own domains and thumbnails
        image_urls = []
        seen = set()

        for url in matches:
            # Skip if already seen or is a Google domain
            if url in seen:
                continue
            if any(domain in url for domain in ['gstatic.com', 'google.com', 'ggpht.com']):
                continue
            if 'encrypted' in url:  # Skip encrypted thumbnails
                continue

            seen.add(url)
            image_urls.append(url)

            if len(image_urls) >= num_images:
                break

        return image_urls

    finally:
        driver.quit()


if __name__ == "__main__":
    # Example usage
    query = "chicken"
    k = 5

    print(f"🔍 Searching Google Images for: '{query}'")
    print(f"📊 Requesting first {k} image URLs...\n")

    urls = get_google_image_urls(query, k)

    print(f"✅ Found {len(urls)} image URLs:\n")
    print(json.dumps(urls, indent=2))

    # Also save to file
    with open('image_urls.json', 'w') as f:
        json.dump({"query": query, "urls": urls}, f, indent=2)

    print(f"\n💾 Saved to image_urls.json")
