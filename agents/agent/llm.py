from typing import Any, Optional, Protocol, Type
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from .prompts import markdown_summariser_prompt, mardown_summariser_system_prompt
import structlog

logger = structlog.get_logger(__name__)

class LLMError(Exception):
    pass

class LLM(Protocol):
    def invoke_mini(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        ...

    def invoke_max(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        ...

class llm_client:
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

        logger.info("Initialised llm_client")

    def _parse_response(self, llm_response: str, parser: PydanticOutputParser) -> BaseModel:
        """Parse the LLMs response to output parser helper"""
        return parser.parse(llm_response)

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

        logger.debug("User Query: ", user_query)

        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_mini_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        if response_schema:
            parsed_response = self._parse_response(llm_response=result, parser=output_parser)
            logger.debug("LLM Mini Result", result=parsed_response.model_dump_json())
            return parsed_response

        logger.debug("LLM Mini Result", result=result.content)
        return result.content

    def invoke_max(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        if response_schema:
            output_parser = PydanticOutputParser(pydantic_object=response_schema)
            instructions = output_parser.get_format_instructions()

            user_query += f"\n\n{instructions}"

        logger.debug("User Query: ", user_query)

        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_max_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        if response_schema:
            parsed_response = self._parse_response(llm_response=result, parser=output_parser)
            logger.debug("LLM Max Result", result=parsed_response.model_dump_json())
            return parsed_response

        logger.debug("LLM Max Result", result=result.content)
        return result.content


def markdown_summariser(title: str, markdown: str, llm: LLM) -> str:
    """Title: what we want to find in the markdown, Markdown is the str we want to find it in"""
    logger.debug("Started markdown_summariser function")
    logger.debug("Markdown is %s char long", len(markdown))
    user_query = markdown_summariser_prompt(title=title, markdown=markdown)
    response = llm.invoke_mini(system_query=mardown_summariser_system_prompt, user_query=user_query)

    logger.debug("LLM Max Result", result=response)
    return response  # invoke_mini already returns a string