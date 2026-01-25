import re
import structlog

logger = structlog.getLogger(__name__)

def clean_markdown(markdown: str) -> str:
    """
    Remove junk from scraped markdown to reduce token costs.

    Removes:
    - Image references (![alt](url))
    - CDN URLs with query parameters
    - Navigation links (Skip to content, etc.)
    - Cart/UI text
    - Multiple consecutive newlines
    - Common UI button text

    This can reduce markdown size by 80-90%, saving significant LLM costs.
    """
    if not markdown:
        return ""

    original_length = len(markdown)

    # Remove image references (![alt](url))
    markdown = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)

    # Remove standalone CDN URLs with query params (png, jpg, etc.)
    markdown = re.sub(r'https?://[^\s)]+\.(png|jpg|jpeg|gif|webp)[^\s)]*', '', markdown)

    # Remove URLs with version/width query params (CDN cruft)
    markdown = re.sub(r'https?://[^\s)]+\?v=\d+[^\s)]*', '', markdown)

    # Remove navigation links
    markdown = re.sub(r'\[Skip to .*?\]\(.*?\)', '', markdown)
    markdown = re.sub(r'\[Continue shopping\]\(.*?\)', '', markdown)

    # Remove cart UI text
    markdown = re.sub(r'Your cart is empty', '', markdown)
    markdown = re.sub(r'\d+Your cart is empty', '', markdown)

    # Remove standalone UI button text
    markdown = re.sub(r'\b(Close|Clear|ClearClose)\b', '', markdown)

    # Remove multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Remove multiple consecutive spaces
    markdown = re.sub(r' {2,}', ' ', markdown)

    cleaned = markdown.strip()
    cleaned_length = len(cleaned)
    reduction = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0

    logger.debug(
        "Cleaned markdown",
        original_length=original_length,
        cleaned_length=cleaned_length,
        reduction_percent=f"{reduction:.1f}%"
    )

    return cleaned