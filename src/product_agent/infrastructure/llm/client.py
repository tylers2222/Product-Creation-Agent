import inspect
from typing import Protocol, Type
import structlog
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from google import genai
from google.genai import types
import datetime

from .prompts import markdown_summariser_prompt, mardown_summariser_system_prompt, GEMINI_MARKDOWN_SUMMARISER_PROMPT
from .utils import _parse_response
from ...models.llm_input import LLMInput

logger = structlog.get_logger(__name__)

class LLMError(Exception):
    pass

class LLM(Protocol):
    """A Protocol defining the methods an LLM should have"""
    async def invoke(self, llm_input: LLMInput) -> str | BaseModel:
        ...

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

class GeminiClient:
    """A class that holds concrete gemini specific impls"""
    def __init__(self, api_key: str):
        self.api_client = genai.Client(
            vertexai=True,
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

        system_cache = self.api_client.caches.create(
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

        response = self.api_client.models.generate_content(
            model=llm_input.model,
            contents=llm_input.user_query,
            config=types.GenerateContentConfig(
                system_instruction=llm_input.system_query if llm_input.system_query else None,
                cached_content=self.system_cache_name if llm_input.cache_wanted else None,
                temperature=0.1
            )
        )

        logger.debug("Completed %s", inspect.stack()[0][3], cached_tokens_used=response.usage_metadata.cached_content_token_count)
        return response