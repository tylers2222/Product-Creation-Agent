from langchain_openai import ChatOpenAI
from firecrawl_api.client import DataResult
import logging
import traceback

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.3
)

"""
Add scoped logs
"""

class SummarisationError(Exception):
    pass

def markdown_summariser(title: str, markdown: str) -> str:
    """Invoke the LLM to cut markdown to stop max token limits"""

    query = f"""You are a markdown extraction specialist. Your task is to trim website markdown to only the relevant product information.

TARGET PRODUCT: {title}

STEP 1: LOCATE PRODUCT CONTENT
Scan the markdown and identify where product information begins and ends.

Look for sections containing:
- Product name/title matching "{title}"
- Product descriptions
- Pricing information
- Product specifications
- Features and benefits
- Size/flavor/variant options
- Ingredients or technical details
- Customer reviews (if present)

STEP 2: IDENTIFY BOUNDARIES
Mark where to START cutting:
- Navigation menus
- Site headers
- Breadcrumbs
- Search bars
- Account/cart elements
- Promotional banners above the product

Mark where to STOP cutting:
- Footer navigation
- Newsletter signups
- Related products sections
- Site-wide promotional content
- Copyright notices
- Footer links

STEP 3: APPLY SAFETY MARGIN
Keep 2-3 lines of context BEFORE the product content starts
Keep 2-3 lines of context AFTER the product content ends

This prevents accidentally cutting:
- Product title formatting
- Price display elements
- Add to cart functionality context
- Important product metadata

STEP 4: REMOVE UNNECESSARY MIDDLE SECTIONS
If the product content contains large irrelevant sections, remove:
- Embedded video players
- Social media widgets
- "You may also like" sections
- Large advertising blocks
- Unrelated blog content

KEEP sections that might seem tangential but could contain product info:
- Tabs (Description, Ingredients, Reviews)
- Accordion sections
- Image galleries
- Size charts

STEP 5: RETURN TRIMMED MARKDOWN
Return just the trimmed mardown only

The output should be markdown that:
- Starts near where product information begins
- Ends near where product information ends
- Removes navigation/footer clutter
- Preserves all product-relevant content
- Includes small safety margins

MARKDOWN TO PROCESS:
{markdown}
    """
    result = llm.invoke(query)
    if not result:
        # Shouldnt return none so raise for error
        logging.error("No result returned")
        raise SummarisationError("None returned from LLM call")

    return result