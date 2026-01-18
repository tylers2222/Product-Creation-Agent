import structlog
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

logger = structlog.getLogger(__name__)

def _parse_response(llm_response: str, parser: PydanticOutputParser) -> BaseModel:
        """Parse the LLMs response to output parser helper"""
        logger.debug("llm_response Type", the_type=type(llm_response))
        return parser.parse(llm_response)