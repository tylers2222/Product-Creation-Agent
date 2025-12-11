from .agent_updated import AgentState

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

def search_agent(state: AgentState) -> str:
    """
    Executes a ReAct-style agent that processes a user query.

    This function takes the current state (which includes the user's question),
    creates an agent using an LLM and the and conndenses the users natural text into business specific text,
    then runs the agent to get a response. The final answer is returned as updated state.

    STEP 1: VALIDATE USER INPUT

    Your job is to UNDERSTAND what the user is asking for, regardless of how they phrase it.

    For EACH variant the user mentions, you need to find:
    1. Size/quantity (5lb, 2kg, 1000g, etc.)
    2. Flavor/variant type (Chocolate, Vanilla, etc.) - if applicable
    3. Price (any mention of cost/price/dollars)
    4. SKU (any product code/SKU/item number)
    5. Barcode (any barcode/UPC/barcode number)

    Examples of valid inputs (all different formats):
    - "5lb Chocolate $59.95 SKU:523525 Barcode:321542352"
    - "Optimum Nutrition 5lb in Chocolate, the SKU is 523525 and barcode is 321542352, Price $59.95"
    - "I need the chocolate 5 pound version for $59.95, our SKU 523525, barcode 321542352"
    - "Product: 5lb choc, costs $60, code 523525, UPC 321542352"

    All of these are VALID - they all contain the 5 required pieces of information.

    For EACH distinct size/flavor combination, verify you can extract all 5 fields.
    If ANY field is missing for ANY variant, list what's missing and ask for it.
    If ALL fields are present for ALL variants, proceed to STEP 2.

    Do NOT require a specific format. Use your understanding to extract the information.

    Args:
        state (AgentState): A dictionary containing the the user's original query.

    Returns:
        dict: Updated state with the generated answer.
    """
    agent = create_tool_calling_agent(llm, [serper_search])
    result = agent.invoke({"messages": state["user_query"]})
    return {"answer": result["messages"][-1].content}