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

logger = structlog.get_logger(__name__)

class LLMError(Exception):
    pass

class LLM(Protocol):
    """A """
    def invoke_mini(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        ...

    def invoke_max(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        ...

class open_ai_client:
    """A concrete impl of the open ai LLM's"""
    def __init__(self):
        self.llm_mini_deterministic = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            verbose=False
        )

        self.llm_max_deterministic = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            verbose=False
        )

        logger.info("Initialised open_ai_client")

    def invoke_mini(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        """ 
        Args:
            system_query: If you want to specify a query that the system acts like
                example: You are a product research specialist
            
            user_query: The users question to the model, dont include format instructions

            model_repsonse: A pydantic model to structure the response into
        """
        logger.debug("Started invoke_mini class function", system_query= system_query is not None, response_schema=response_schema is not None)
        
        if response_schema:
            output_parser = PydanticOutputParser(pydantic_object=response_schema)
            instructions = output_parser.get_format_instructions()

            user_query += f"\n\n{instructions}"

        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_mini_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        if response_schema:
            parsed_response = _parse_response(llm_response=result.content, parser=output_parser)
            logger.debug("LLM Mini Result", result=parsed_response.model_dump_json())
            return parsed_response

        logger.debug("LLM Mini Result", result=result.content)
        return result.content

    def invoke_max(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        if response_schema:
            output_parser = PydanticOutputParser(pydantic_object=response_schema)
            instructions = output_parser.get_format_instructions()

            user_query += f"\n\n{instructions}"

        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_max_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        if response_schema:
            parsed_response = _parse_response(llm_response=result.content, parser=output_parser)
            logger.debug("LLM Max Result", result=parsed_response.model_dump_json())
            return parsed_response

        logger.debug("LLM Max Result", result=result.content)
        return result.content

class MarkdownLLM:
    """A class that holds concrete markdown specific impls"""
    def __init__(self, api_key: str):
        self.api_client = genai.Client(api_key=api_key)
        self.system_cache_name = "markdown_summariser"

    def _generate_cache(self):
        logger.debug("Starting %s", inspect.stack()[0][3])

        system_cache = self.api_client.caches.create(
            model="gemini-1.5-flash",
            config=types.CreateCachedContentConfig(
                system_instruction=GEMINI_MARKDOWN_SUMMARISER_PROMPT,
                display_name="markdown_summariser",
                ttl=datetime.timedelta(days=30)
            )
        )
        return system_cache

    def invoke_mini(self, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        logger.debug("Starting %s", inspect.stack()[0][3])

        response = self.api_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_query,
            config=types.GenerateContentConfig(
                cached_content=self.system_cache_name,
            )
        )
        logger.debug("Completed %s", inspect.stack()[0][3])
        return response

def markdown_summariser(title: str, markdown: str, llm: LLM) -> str:
    """Title: what we want to find in the markdown, Markdown is the str we want to find it in"""
    logger.debug("Started markdown_summariser function")
    logger.debug("Markdown is %s char long", len(markdown))
    user_query = markdown_summariser_prompt(title=title, markdown=markdown)
    response = llm.invoke_mini(system_query=mardown_summariser_system_prompt, user_query=user_query)

    logger.debug("LLM Max Result", result=response)
    return response  # invoke_mini already returns a string