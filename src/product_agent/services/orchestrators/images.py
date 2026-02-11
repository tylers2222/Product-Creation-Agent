from product_agent.models.shopify import Variant
from product_agent.utils.image_bytes_cleaner import clean_image_bytes
from pydantic import BaseModel
import structlog

from google.genai import types

from product_agent.core.agent_configs.image_classification import IMAGE_CLASSIFICATION_SYSTEM_PROMPT
from product_agent.infrastructure.llm.client import LLM
from product_agent.models.image_classification import ImageRelevanceResponse
from product_agent.models.llm_input import LLMInput
from product_agent.services.infrastructure.llm import llm_service

logger = structlog.getLogger(__name__)

class Image(BaseModel):
    url:            str
    image_bytes:    bytes
class ImageRequestScructure(BaseModel):
    images: list[Image]
    variants: list[Variant]
    query: str

async def image_matching_svc(
    variants: list,
    images_bytes_data: dict,
    llm: LLM,
    model: str):
    """
    LLM matches image data to specific variants wanted by the user
    """
    logger.debug(
        "Starting image matching using %s", model,
        length_variants=len(variants),
        length_image_data=len(images_bytes_data)
    )
    images_bytes_data_clean = clean_image_bytes(images_bytes_data)
    # invoke gemini for images here
    

async def classify_image_svc(
    query: str,
    images_bytes_data: dict,
    llm: LLM,
    model: str) -> ImageRelevanceResponse:
    """
    Classify images via LLM in the service layer
    """
    images_bytes_data_clean = clean_image_bytes(images_bytes_data)
    logger.debug("Cleaned image bytes data", length_data=len(images_bytes_data_clean))
    user_query = []

    if "gemini" in model:
        user_query.append(
            types.Part.from_text(text=f"Please analyse these {len(images_bytes_data_clean)} images")
        )
        
        for url, image_bytes in images_bytes_data_clean.items():
            user_query.append(
                types.Part.from_text(text=f"Source URL: {url}")
            )
            user_query.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )

        user_query.append(
            types.Part.from_text(text=f"Classify which image is the asked for in the query\nQuery: {query}")
        )
    system_prompt=IMAGE_CLASSIFICATION_SYSTEM_PROMPT
    logger.debug(
        "Sending query to image classification model",
        model=model,
        len_system_prompt=len(system_prompt),
        len_user_query=len(user_query),
        user_query=user_query
    )

    llm_input = LLMInput(
        model=model,
        system_query=system_prompt,
        user_query=user_query,
        response_schema=ImageRelevanceResponse
    )

    return await llm_service(llm_input=llm_input, llm=llm)
