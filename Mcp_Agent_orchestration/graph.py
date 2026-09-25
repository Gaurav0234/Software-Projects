import sys

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from config import GROQ_API_KEY, GROQ_MODEL
def route_after_agent(state: MessagesState) -> str:
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", []):
        return "tools"

    return END


async def build_graph():
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

    mcp_client = MultiServerMCPClient(
        {
            "assignment_tools": {
                "command": sys.executable,
                "args": ["-m", "mcp_servers.server"],
                "transport": "stdio",
            }
        }
    )

    tools = await mcp_client.get_tools()

    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY,
    )

    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: MessagesState) -> dict:
        response: AIMessage = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}



    builder = StateGraph(MessagesState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        ["tools", END],
    )
    builder.add_edge("tools", "agent")

    return builder.compile()
