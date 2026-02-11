import requests
from requests import Timeout

async def get_bytes(image_url: str):
    """Utils helper to get base64 from URL"""
    return requests.get(image_url, timeout=10000).content