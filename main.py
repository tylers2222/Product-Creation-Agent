"""
Simple Google Images URL scraper
Returns first K image URLs for a given search query
"""
import time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

DRIVER_PATH = "/Users/tylerstewart/Downloads/chromedriver-mac-arm64-2/chromedriver"

def get_google_image_urls(query: str, num_images: int = 10) -> list:
    """
    Get the first K image URLs from Google Images for a search query.

    Clicks thumbnails to reveal preview panel, extracts image src from preview.

    Args:
        query: Search term (e.g., "chicken")
        num_images: Number of image URLs to return (default 10)

    Returns:
        List of image URLs
    """
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    try:
        # Navigate to Google Images
        search_url = f"https://www.google.com/search?tbm=isch&q={query}"
        driver.get(search_url)
        time.sleep(2)

        # Find all thumbnail images (includes data:image base64 thumbnails)
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

        if not thumbnails:
            print("⚠️  No thumbnails found!")
            return []

        print(f"📸 Found {len(thumbnails)} thumbnails\n")

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
                                    print(f"✅ [{i+1}] {src[:80]}...")
                                    url_found = True
                                    break
                            except:
                                continue

                        if url_found:
                            break
                    except:
                        continue

                if not url_found:
                    print(f"⚠️  [{i+1}] No image URL found in preview")

            except Exception as e:
                print(f"❌ [{i+1}] Error: {str(e)[:50]}")
                continue

        return image_urls

    finally:
        driver.quit()


if __name__ == "__main__":
    # Example usage
    query = "Optimum Nutrition Gold Standard 100% Whey 5lb strawberry buy online product photo"
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
