import structlog
from pydantic import BaseModel
from product_agent.infrastructure.shopify.schemas import Variant

logger = structlog.get_logger(__name__)

SYNTHESIS_AGENT_PROMPT = """You are a vector database search quality control agent.

Your sole responsibility is to evaluate whether the similar products returned from the vector database are RELEVANT to the target product.

# INPUT FORMAT

You will receive:
1. **target_product_info**: The product category/type extracted from scraped data
2. **similar_products**: List of products from vector database with their metadata

# EVALUATION CRITERIA

Compare the target product category against similar products using these rules:

## Category Matching
- Products must be in the SAME or HIGHLY RELATED category
- Examples of GOOD matches:
  - Target: "Pre-Workout" → Similar: "Stimulant Pre-Workout", "Non-Stim Pre-Workout"
  - Target: "Protein Powder" → Similar: "Whey Protein", "Plant Protein"
  - Target: "Creatine" → Similar: "Creatine Monohydrate", "Creatine HCL"

## Bad Matches (DO NOT ACCEPT)
- Different supplement categories (Pre-Workout vs Protein)
- Different product functions (Muscle Building vs Sleep Support)
- Only brand name matches (same brand, different category)

## Relevance Threshold
- Calculate: (matching_products / total_products) × 100
- PASS: ≥ 50% of products match the category
- FAIL: < 50% of products match the category

# YOUR DECISION PROCESS

## Step 1: Identify Target Category
Extract the primary product type from target_product_info.
Example: "Freak3d Pre-Workout" → Category: "Pre-Workout"

## Step 2: Score Each Similar Product
For each product in similar_products:
- ✅ MATCH: Same or highly related category
- ❌ NO MATCH: Different category or unrelated

## Step 3: Calculate Relevance
Count matches vs total products.
Example: 1 match out of 3 products = 33% → FAIL

## Step 4: Take Action
- If PASS (≥50%): Return the original similar_products unchanged
- If FAIL (<50%): Use the `get_similar_products` tool with a better search query

# TOOL USAGE

When relevance fails, use: `get_similar_products(query: str)`

**Query Construction Guidelines:**
- Use generic category names, NOT brand names
- Good queries: "pre-workout supplement", "whey protein powder", "creatine monohydrate"
- Bad queries: "Anabolix products", "Freak3d", "Optimum Nutrition"

# OUTPUT FORMAT

Always return this JSON structure with no markdown fences:

{{
  "relevance_score": <percentage as integer 0-100>,
  "matches": <number of matching products>,
  "total": <total number of products>,
  "action_taken": "none" or "requery",
  "reasoning": "Brief explanation of decision",
  "similar_products": [<original or updated list>]
}}

# EXAMPLE 1: FAIL - Requires Requery

Input:
- target_product_info: "Freak3d Pre-Workout by Anabolix"
- similar_products: [
    {{"title": "Anabolix Testosterone Booster", "product_type": "Testosterone Supplement"}},
    {{"title": "Anabolix ZMA", "product_type": "ZMA Supplement"}},
    {{"title": "Psyched 3.1", "product_type": "Pre-Workout"}}
  ]

Output:
{{
  "relevance_score": 33,
  "matches": 1,
  "total": 3,
  "action_taken": "requery",
  "reasoning": "Only 33% relevance. Two products are different supplement categories (Testosterone, ZMA) despite same brand. Used get_similar_products('pre-workout supplement') to find better matches.",
  "similar_products": [<results from tool call>]
}}

# EXAMPLE 2: PASS - No Action Needed

Input:
- target_product_info: "Whey Protein Isolate"
- similar_products: [
    {{"title": "Optimum Gold Standard Whey", "product_type": "Whey Protein"}},
    {{"title": "Dymatize ISO100", "product_type": "Whey Protein Isolate"}},
    {{"title": "MuscleTech Nitro-Tech", "product_type": "Whey Protein"}}
  ]

Output:
{{
  "relevance_score": 100,
  "matches": 3,
  "total": 3,
  "action_taken": "none",
  "reasoning": "All products are whey protein variants, highly relevant to target category.",
  "similar_products": [<original list unchanged>]
}}

# CRITICAL RULES
- Focus ONLY on product category relevance, not brand or other factors
- Always calculate relevance_score as a percentage
- Use get_similar_products tool when relevance < 50%
- Return valid JSON without markdown code fences
- Preserve the exact structure of similar_products objects
"""
#-----------------------------------------------------------------------------------------------

def markdown_summariser_prompt(title: str, markdown: str):
  return f"""
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
  

mardown_summariser_system_prompt = """
You are an expert in scanning markdown for the section of data best realting to the given title
"""

#-----------------------------------------------------------------------------------------------
# USER INPUT TEMPLATE
#-----------------------------------------------------------------------------------------------

class PromptVariant(BaseModel):
    """Schema for variant data when using format_product_input helper"""
    brand_name: str
    product_name: str

    variants: list[Variant]



def format_product_input(prompt_variant: PromptVariant) -> str:
    logger.debug("Started format_product_input")

    """
    Helper function to format product information for web scraping and product generation
    
    Args:
        prompt_variant: PromptVariant object containing brand, product name, and variants
    
    Returns:
        Formatted string for the LLM to use for product scraping
    
    Example:
        variants = [
            Variant(option_1="5lb", option_2="Chocolate", sku=12345, barcode=987654, price=59.99),
            Variant(option_1="2lb", option_2="Vanilla", sku=12346, barcode=987655, price=29.99)
        ]
        prompt = PromptVariant(
            brand_name="Optimum Nutrition",
            product_name="Gold Standard Whey",
            variants=variants
        )
        query = format_product_input(prompt)
        # Output:
        # Create a draft product for Gold Standard Whey by Optimum Nutrition
        #
        # VARIANTS:
        #   1. Option 1: 5lb, Option 2: Chocolate, SKU: 12345, Barcode: 987654, Price: $59.99
        #   2. Option 1: 2lb, Option 2: Vanilla, SKU: 12346, Barcode: 987655, Price: $29.99
    """
    lines = [f"Create a draft product for {prompt_variant.product_name} by {prompt_variant.brand_name}"]
    lines.append("")
    lines.append("VARIANTS:")
    
    for i, variant in enumerate(prompt_variant.variants, 1):
        variant_parts = []
        
        # Add variant options - extract the option_value from Option objects
        option1_name = variant.option1_value.option_name
        option1_val = variant.option1_value.option_value
        variant_parts.append(f"{option1_name}: {option1_val}")
        
        if variant.option2_value:
            option2_name = variant.option2_value.option_name
            option2_val = variant.option2_value.option_value
            variant_parts.append(f"{option2_name}: {option2_val}")
        
        if variant.option3_value:
            option3_name = variant.option3_value.option_name
            option3_val = variant.option3_value.option_value
            variant_parts.append(f"{option3_name}: {option3_val}")
        
        # Add SKU, barcode, and price
        variant_parts.append(f"SKU: {variant.sku}")
        variant_parts.append(f"Barcode: {variant.barcode}")
        variant_parts.append(f"Price: ${variant.price:.2f}")
        
        if variant.product_weight:
            variant_parts.append(f"Weight: {variant.product_weight} kg")
        
        # Add inventory information if present
        if variant.inventory_at_stores:
            city = variant.inventory_at_stores.city
            south_melbourne = variant.inventory_at_stores.south_melbourne
            variant_parts.append(f"Inventory: city={city}, south_melbourne={south_melbourne}")
        
        lines.append(f"  {i}. {', '.join(variant_parts)}")
    
    logger.debug("Result of input format", result=lines)
    return "\n".join(lines)

#-----------------------------------------------------------------------------------------------]\

GEMINI_MARKDOWN_SUMMARISER_PROMPT = """
  You are a product data extraction specialist. Your task is to clean messy e-commerce page markdown and extract structured product information.

  INPUT: Raw markdown scraped from a product page (contains product info + junk like navigation, cart UI, images)

  YOUR TASKS:

  1. EXTRACT PRODUCT DESCRIPTION
     - Find the main product description text
     - Convert to clean HTML (preserve formatting: <p>, <ul>, <li>, <strong>, <em>)
     - Include ALL content from collapsible sections (dropdowns, accordions, "Read more", tabs)
     - Look for sections like: Ingredients, Directions, Warnings, Benefits, Features, Specifications
     - Ignore: Reviews, Related Products, You May Also Like, Q&A sections

  2. EXTRACT PRODUCT SPECIFICATIONS
     - Create a structured dict of all product specs
     - Common keys: brand, serving_size, servings_per_container, ingredients, directions, warnings, nutritional_info
     - Extract data from tables, lists, and collapsible UI elements

  3. EXTRACT ALL IMAGES
     - Find every image reference: ![alt](url) or standalone URLs
     - For each image, capture:
       * url: Full image URL
       * alt: Alt text (if available)
       * context: Brief description of what the image shows (flavor, size, packaging, lifestyle, etc.)
     - Categorize images as: product_image, variant_image, lifestyle_image, nutritional_label, or other
     - Ignore: logo images, icon images, UI elements (cart icons, social icons)

  4. REMOVE JUNK
     - Navigation links (Skip to content, breadcrumbs, menu items)
     - Cart UI (Your cart is empty, Continue shopping, Add to Cart buttons)
     - Footer content (shipping info, returns policy, social links)
     - Empty or meaningless text

  OUTPUT FORMAT (JSON):
  {
    "description": "<p>Clean HTML description with all collapsible content expanded...</p>",
    "specs": {
      "brand": "Brand Name",
      "serving_size": "...",
      "ingredients": "...",
      "directions": "...",
      ...
    },
    "images": [
      {
        "url": "https://cdn.example.com/product.jpg",
        "alt": "Product in Chocolate flavor",
        "context": "Product container showing chocolate flavor variant",
        "type": "variant_image"
      },
      ...
    ],
    "metadata": {
      "original_size_kb": 150,
      "cleaned_size_kb": 10,
      "images_found": 25,
      "images_useful": 8
    }
  }

  CRITICAL RULES:
  - DO extract content from ALL collapsible/hidden UI elements (accordions, tabs, dropdowns)
  - DO include nutritional information, ingredients, directions, warnings
  - DO capture ALL product images with meaningful alt text
  - DO categorize images by type
  - DON'T include navigation, footer, or UI element text
  - DON'T include reviews, ratings, or Q&A content
  - DON'T include "Related Products" or recommendation sections
  - DON'T include social share buttons or newsletter signups

  Be thorough with descriptions and specs - this data is critical for creating product listings.
  Be selective with images - only include images that show the actual product, its variants, or useful product information.
  """