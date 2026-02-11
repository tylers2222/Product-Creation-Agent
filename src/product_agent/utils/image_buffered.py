import io

def images_to_buffered(images: list[bytes]) -> list:
    """
    Giving image bytes a buffered piece of memory for uploading places
    """
    return [io.BytesIO(i) for i in images]