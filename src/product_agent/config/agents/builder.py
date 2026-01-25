import inspect
import structlog

from typing import Any, Callable, Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import StructuredTool

from ..container import ServiceContainer
from .synthesis_build import build_synthesis_agent
from .config import AgentConfig

logger = structlog.getLogger(__name__)

class AgentFactory:
    """
    Class that can build agents and have them automatically built internally
    """
    def __init__(self, service_container: ServiceContainer):
        self.agents = 0
        self.dependencies = service_container

    def _build_llm(self, model: str):
        """Helps map a model to building the LLM for an agent"""
        logger.debug("Starting %s", inspect.stack()[0][3])

        if "gpt" in model:
            logger.debug("Found Open Ai LLM")
            return ChatOpenAI(
                model=model,
                temperature=0.1,
                max_retries=2
            )

        if "claude" in model:
            logger.debug("Found Anthropic")
            return ChatAnthropic(
                model=model,
                temperature=0.1,
                max_retries=2
            )

        if "gemini" in model:
            logger.debug("Found Anthropic")
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=0.1,
                max_retries=2
            )

        raise ValueError(f"LLM {model} not supported in infrastructure")

    def build_custom_agent(self, setup: AgentConfig):
        """Build a custom agent on the fly with input params"""
        logger.debug("Starting %s", inspect.stack()[0][3], config=setup)

        llm = self._build_llm(model=setup.model)
        prompt = ChatPromptTemplate.from_messages([
            ("system", setup.system_prompt if setup.system_prompt is not None else "You are a smart Ai Agent pickup the area of expertise the user is asking for and act like a professional in that area"),
            ("user", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        agent = create_tool_calling_agent(llm=llm, tools=setup.tools, prompt=prompt)
        return AgentExecutor(agent=agent, tools=setup.tools, verbose=True)
    
    def build_synthesis_agent(self, agent_config: AgentConfig):
        """Build the known synthesis agent we built internally"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        synthesis_agent = build_synthesis_agent(container=self.dependencies, config_settings=agent_config)
        logger.debug("Returned Agent: %s", synthesis_agent is not None)
        return synthesis_agent
