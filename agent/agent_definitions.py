from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from .tools import mark
import os

def create_synthesis_agent():
    agent = create_tool_calling_agent(
        llm = ChatOpenAI(
            model = "gpt-4o-mini",
            temperature = 0.1
        ),
        tools=[],
    )