import structlog

logger = structlog.getLogger(__name__)

def calculate_image_size(images: list[bytes]) -> int:
    """Return how many mb of data the image takes"""
    image_to_kb = sum(len(i) for i in images) / 1024
    image_to_mb = image_to_kb / 1024
    logger.debug("Image data's mb", mb=int(image_to_mb))

    return (image_to_mb)
