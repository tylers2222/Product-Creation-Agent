from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .prompts import SYNTHESIS_AGENT_PROMPT

def synthesis_agent(tools: list):
    """An agent that analyses the strength of similarity search for vector searches"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTHESIS_AGENT_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(
        model = "gpt-4o",
        temperature = 0.1
    )
    
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    return AgentExecutor(agent=agent, tools=tools, verbose=False)