import asyncio
import base64
import hashlib
import inspect
import datetime
import io
from typing import Protocol
from product_agent.models.image_transformer import ImageTransformer
from product_agent.utils.image_size_calc import calculate_image_size
import structlog
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from .utils import _parse_response
from ...models.llm_input import LLMInput

logger = structlog.get_logger(__name__)

class LLMError(Exception):
    pass

class LLM(Protocol):
    """A Protocol defining the methods an LLM should have"""
    async def invoke(self, llm_input: LLMInput) -> str | BaseModel:
        """Protocol how to invoke LLM class method"""
        ...

    async def transform_for_images(self, data: ImageTransformer):
        """Protocol on how to structure queries with img data"""

class OpenAiClient:
    """A concrete impl of the open ai LLM's"""
    def __init__(self, api_key: str):
        self._model_configs = {
            "scraper_mini": {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
            },
            "max_deterministic": {
                "model": "gpt-4o",
                "temperature": 0.1,
            }
        }

        self._api_key = api_key
        logger.info("Initialised OpenAiClient")

    def _resolve_model(self, model: str):
        """
        Resolve what model we want to use
        
        Sometimes a part of the codebase just wants to resolve to the best scraper
        and doesnt want to config a model specifically just connect to "scraper"
        """
        if "-" not in model:
            return self._model_configs[model]["model"]
        
        return model

    async def invoke(self, llm_input: LLMInput) -> str | BaseModel:
        """ 
        Args:
            system_query: If you want to specify a query that the system acts like
                example: You are a product research specialist
            
            user_query: The users question to the model, dont include format instructions

            model_repsonse: A pydantic model to structure the response into
        """
        logger.debug("Starting %s", inspect.stack()[0][3],
            llm_model=llm_input.model,
            system_query=llm_input.system_query is not None,
            cache_wanted=llm_input.cache_wanted,
        )
        model = self._resolve_model(llm_input.model)

        model = self._resolve_model(llm_input.model)
        llm_input.model = model
        model_object = ChatOpenAI(
            model=llm_input.model,
            verbose=llm_input.verbose,
            api_key=self._api_key
        )
        
        if llm_input.response_schema:
            output_parser = PydanticOutputParser(pydantic_object=llm_input.response_schema)
            instructions = output_parser.get_format_instructions()

            llm_input.user_query += f"\n\n{instructions}"

        invocation: list[dict] = []
        if llm_input.system_query is not None:
            invocation.append({"role": "system", "content": llm_input.system_query})

        invocation.append({"role": "user", "content": llm_input.user_query})

        result = model_object.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        if llm_input.response_schema:
            parsed_response = _parse_response(llm_response=result.content, parser=output_parser)
            logger.debug("LLM Mini Result", result=parsed_response.model_dump_json())
            return parsed_response

        logger.debug("LLM Mini Result", result=result.content)
        # Theres also meta data there if its wanted including tokens used etc
        return result.content

    async def transform_for_images(self, data: ImageTransformer):
        """Transform raw data ready for specific LLM provider"""
        image_len = data.how_many_images()
        if image_len > 50:
            raise Exception("ChatGPT max images is 50: Request %s", image_len)

        user_query = []
        for message in data.order:
            if message.type == "query":
                user_query.append({
                    "type": "input_text",
                    "text": message.query
                })
            else:
                user_query.append({
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64.b64encode(message.image_bytes).decode()}"
                })
        logger.debug("OpenAi User query complete", len_user_query=len(user_query))
        return user_query

class GeminiClient:
    """A class that holds concrete gemini specific impls"""
    def __init__(self, api_key: str):
        self.vertex_api_client = genai.Client(
            vertexai=True,
            project="gen-lang-client-0384813764",
            location="global"
        )

        self.developer_api_client = genai.Client(
            project="gen-lang-client-0384813764",
            location="us-central1"
        )
        self.system_cache_name = "scraper_prompt"

        self._model_configs = {
            "scraper_mini": {
                "model": "gemini-2.5-flash",
                "temperature": 0.1,
            }
        }

    def _generate_cache(self, system_prompt: str, time_wanted: int):
        logger.debug("Starting %s", inspect.stack()[0][3])

        system_cache = self.vertex_api_client.caches.create(
            model="gemini-2.0-flash",
            config=types.CreateCachedContentConfig(
                system_instruction=system_prompt,
                display_name="scraper_prompt",
                ttl=datetime.timedelta(minutes=time_wanted)
            )
        )
        return system_cache

    async def invoke(self, llm_input: LLMInput) -> str | BaseModel:
        """
        Invoke Gemini model with given input.

        Args:
            llm_input: LLMInput containing query and optional schema
            cache_wanted: Does this run want to use a cached system prompt

        Returns:
            String response or structured BaseModel
        """
        logger.debug("Starting %s", inspect.stack()[0][3],
            llm_model=llm_input.model,
            system_query=llm_input.system_query is not None,
            cache_wanted=llm_input.cache_wanted,
        )

        if "-" not in llm_input.model:
            llm_input.model = self._model_configs[llm_input.model]["model"]

        if llm_input.cache_wanted:
            self._generate_cache(system_prompt=llm_input.system_query, time_wanted=5)

        response = self.vertex_api_client.models.generate_content(
            model=llm_input.model,
            contents=llm_input.user_query,
            config=types.GenerateContentConfig(
                system_instruction=llm_input.system_query if llm_input.system_query else None,
                cached_content=self.system_cache_name if llm_input.cache_wanted else None,
                temperature=0.1,
                response_mime_type="application/json" if llm_input.response_schema else "text/plain",
                response_schema=llm_input.response_schema if llm_input.response_schema else None
            )
        )

        logger.debug("Returned llm response", response=response.text)
        logger.debug("Completed %s", inspect.stack()[0][3], cached_tokens_used=response.usage_metadata.cached_content_token_count)

        return response.text

    async def transform_for_images(self, data: ImageTransformer):
        """
        Transform raw data ready for specific LLM provider
        
        Note:
            This looks like business logic creep into infrastructure
            Becuase a workflow is LLM agnostic, it needs to be attached to the client
            Otherwise it has to call a service based on the type in the service layer
            Instead of just calling its transform
        """
        logger.debug("Starting %s",
            inspect.stack()[0][3],
        )

        # Pass the whole query as bytes to the utils helper
        # The inline gemini bytes passing allows a max of 20mb
        # IF over then we will need to use the file api
        total_query_size = calculate_image_size(
            images=[d.turn_to_bytes() for d in data.order]
        )

        logger.debug("Total image based query size", size=total_query_size)
        
        # Used to return value for gemini specific request
        user_query = []

        if total_query_size >= 20:
            # If its over 20mb it will need to be done via the file api
            logger.debug("Starting process for request over 20mb")
            coros = []
            for d in data.order:
                if d.type == "image":
                    coros.append(self.upload_to_file_api(
                        url=d.url,
                        image_file=io.BytesIO(d.image_bytes)
                    ))

            file_results = await asyncio.gather(*coros)
            # This is used to track what index of image we are on
            # and need to pull from the success list
            latest_image_index = 0
            for d in data.order:
                if d.type == "image":
                    user_query.append(file_results[latest_image_index])
                    latest_image_index += 1
                if d.type == "query":
                    user_query.append(types.Part.from_text(text=str(d.query)))

            return user_query

        # Total query mb is below 20
        for d in data.order:
            if d.type == "image":
                user_query.append(types.Part.from_bytes(
                    data=d.image_bytes,
                    mime_type="image/jpeg"
                ))

            if d.type == "query":
                user_query.append(types.Part.from_text(text=str(d.query)))

        logger.debug("Gemini user_query completed", user_query=user_query)
        return user_query
    
    async def upload_to_file_api(
        self,
        url: str,
        image_file: str | io.IOBase
    ):
        """
        Upload to the file api
        
        Note: The file name is automatically hashed to meet Gemini API requirements
        (only lowercase alphanumeric + dashes allowed)
        """
        # Hash the URL to create a valid file name
        # Gemini File API only allows: lowercase alphanumeric + dashes
        file_name = f"img-{hashlib.md5(url.encode()).hexdigest()}"

        try:
            return self.developer_api_client.files.upload(
                file=image_file,
                config={"name": file_name, "mime_type": "image/jpeg"}
            )

        except ClientError as ce:
            logger.debug("Already exists error, trying get method")
            if "ALREADY_EXISTS" in str(ce):
                return self.developer_api_client.files.get(name=file_name)

            raise Exception(ce) from ce
