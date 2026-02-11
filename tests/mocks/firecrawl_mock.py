import structlog
from product_agent.infrastructure.firecrawl.schemas import FireResult
from collections import namedtuple

logger = structlog.getLogger(__name__)

class MockScrapeResult:
    def __init__(self, markdown: str, metadata: dict):
        self.markdown = markdown
        # Convert metadata dict to an object with attributes
        self.metadata = type('obj', (object,), metadata)()

MockSearchData = namedtuple('SearchData', ['web'])

mock_search_data = MockSearchData(web=[
    MockScrapeResult(
        markdown="""# 100% Pure Cream of Rice by Rapid Supplements

## Product Overview
Enjoy a nutritious and hearty bowl of goodness full of complex carbohydrates with 100% Cream of Rice By Rapid Supplements. This hearty meal supplement delivers a sustained energy supply to fuel your workouts.

## Key Features
- 30 grams of carbohydrates per serving
- Pure cream of rice
- Complex carbohydrates for sustained energy
- Easy to digest
- Perfect pre or post workout meal
- Great tasting and easy to prepare

## Nutritional Information
Per 40g serving:
- Energy: 150 cal
- Protein: 2.4g
- Carbohydrates: 33g
- Fat: 0.3g

## Directions
Mix 40g with 200ml water or milk. Microwave for 2 minutes stirring occasionally.""",
        metadata={
            "title": "100% Pure Cream of Rice by Rapid Supplements - Nutrition Warehouse",
            "description": "Enjoy a nutritious and hearty bowl of goodness full of complex carbohydrates with 100% Cream of Rice By Rapid Supplements. This hearty meal supplement delivers a sustained energy supply to fuel your workouts. With 30 grams of carbohydrates per serving, you'll fuel your muscles with the proper nutrients. Order now!",
            "url": "https://www.nutritionwarehouse.com.au/products/100-pure-cream-of-rice-by-rapid-supplements?variant=42569760702691"
        }
    ),
    MockScrapeResult(
        markdown="""# Rapid Supplements Cream of Rice

A premium quality cream of rice supplement perfect for athletes and fitness enthusiasts.

## Benefits
- Sustained energy release
- Easy on digestion
- Naturally flavored
- No artificial sweeteners
- Quick and convenient preparation

Perfect for pre-workout energy or post-workout recovery. Mix with your favorite protein powder for a complete meal.""",
        metadata={
            "title": "Rapid Supplement's – Cream of Rice – Supplement Supply",
            "description": None,
            "url": "https://supplementsupply.com.au/product/rapid-supplements-cream-of-rice/"
        }
    ),
    MockScrapeResult(
        markdown="""# Cream Of Rice 30 Serves

Pure Cream of Rice is a delicious bowl of hearty goodness full of complex carbohydrates to fuel your workouts. Cream of rice can also be consumed as a healthy meal for a sustained energy supply.

## Product Details
- 30 servings per container
- Naturally flavoured
- No artificial sweeteners
- Gentle on the stomach
- Ready in minutes
- Keeps you feeling fuller for longer

## Usage
Ideal for bodybuilders, athletes, and anyone looking for a high-quality carbohydrate source.""",
        metadata={
            "title": "Cream Of Rice 30 Serves\n  \n  \n   – Rapid Supplements",
            "description": "Pure Cream of Rice is a delicious bowl of hearty goodness full of complex carbohydrates to fuel your workouts. Cream of rice can also be consumed as a healthy meal for a sustained energy supply. Naturally flavoured with no artificial sweeteners it is gentle on the stomach, ready in minutes and keeps you feeling fuller ",
            "url": "https://rapidsupps.com.au/products/cream-of-rice"
        }
    ),
    MockScrapeResult(
        markdown="""# 100% Pure Cream of Rice by Rapid Supplements

## Description
100% Pure Cream of Rice by Rapid Supplements is a delicious nutritious bowl of hearty goodness full of complex carbohydrates to fuel your workouts alternatively Cream of Rice can be consumed as a hearty meal for a sustained energy supply.

## Features
- Premium quality cream of rice
- Complex carbohydrates
- Sustained energy
- Easy to prepare
- Great taste
- Excellent for muscle fuel

## Serving Suggestions
Can be mixed with protein powder, fruits, nuts, or enjoyed plain. Perfect for breakfast or as a pre/post workout meal.""",
        metadata={
            "title": " 100% Pure Cream of Rice by Rapid Supplements  \n     – Supplement Warehouse \n",
            "description": "100% Pure Cream of Rice by Rapid Supplements is a delicious nutritious bowl of hearty goodness full of complex carbohydrates to fuel your workouts alternatively Cream of Rice can be consumed as a hearty meal for a sustained energy supply. Order now!",
            "url": "https://www.supplementwarehouse.com.au/products/100-pure-cream-of-rice-by-rapid-supplements"
        }
    )
])

class MockScraperClient:
    def __init__(self):
        pass

    def scrape_and_search_site(self, query: str, limit: int = 5) -> FireResult:
        logger.debug("Called MockScraperClient.scrape_and_search_site", query=query, limit=limit)

        logger.debug("MockScraperClient.scrape_and_search_site returned a FireResult")
        return FireResult(
            data=mock_search_data,
            query="Rapid supplements cream of rice 1.2kg"
        )

    def get_urls_for_query(self, query: str, limit: int = 5):
        """Mock implementation of getting urls"""
        return [
            "www.fasbfjb.com",
            "www.asgagw.com",
            "www.rjhrtyjw.com",
            "www.qgfgs5.com"
        ]

    def scraper_url_to_markdown(self, url: str):
        """Mock implementation of scraper_url_to_markdown."""
        logger.debug("Called MockScraperClient.scraper_url_to_markdown", url=url)

        return {
            "markdown": """# Test Product Page

## Product Details
This is a test product with mock markdown content.

## Features
- Feature 1
- Feature 2
- Feature 3

## Price
$29.99""",
            "metadata": {
                "url": url,
                "title": "Test Product Title"
            }
        }

    def batch_scraper_url_to_markdown(self, urls: list):
        """Mock implementation of batch_scraper_url_to_markdown."""
        logger.debug("Called MockScraperClient.batch_scraper_url_to_markdown", urls=urls)

        # Mock job result
        MockJob = type('Job', (object,), {
            'id': 'mock_job_123',
            'status': 'completed',
            'results': [
                {
                    'markdown': f"""# Product from {url}

## Details
Mock markdown content for {url}""",
                    'metadata': {'url': url}
                } for url in urls
            ]
        })

        return MockJob()
