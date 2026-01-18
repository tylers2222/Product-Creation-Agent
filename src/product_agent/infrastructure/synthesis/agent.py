import structlog

from typing import Any, Protocol
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

logger = structlog.getLogger(__name__)

class Agent(Protocol):
    """Protocol that defines the methods an agent should have"""
    def invoke(self, query: str):
        """A method to get a response from the LLM within the agent"""
        ...

class SynthesisAgent:
    """A Concrete agent"""
    def __init__(self, agent: AgentExecutor):
        """
        Tools in the tool layer, inject it in
        """
        self.agent = agent
        
    def invoke(self, query: str, model: BaseModel | None = None):
        """Invoke an agent for a response"""
        logger.debug("Started agent invoke", query=query, model=model)

        if model:
            output_parser = PydanticOutputParser(pydantic_object=model)
            query += f"\n\n{output_parser.get_format_instructions()}"
        
        result = self.agent.invoke({"input": query})
        logger.debug("Agent Invocation Complete", result=result)
        
        output_text = result.get("output")

        if model:
            model_result = output_parser.parse(output_text)
            return model_result

        # may need to understand the return values keys if we want to start passing no model in the future
        return output_text