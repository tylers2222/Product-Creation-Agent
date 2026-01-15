from typing import Any, Protocol
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage

class Agent(Protocol):
    """Protocol that defines the methods an agent should have"""
    def invoke(self, query: str):
        """A method to get a response from the LLM within the agent"""
        ...

class SynthesisAgent:
    """A Concrete agent"""
    def __init__(self, agent: AgentExecutor):
        self.agent = agent
        
    def invoke(self, query: str):
        """Invoke an agent for a response"""
        self.agent.invoke({"messages": HumanMessage(content=query)})