from langchain_core.messages import AIMessage
from langgraph.graph import END

from graph import route_after_agent


def test_routes_to_tools_when_llm_requests_a_tool():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_weather",
                        "args": {"location": "Bangalore"},
                        "id": "weather-1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }

    result = route_after_agent(state)

    assert result == "tools"


def test_ends_when_llm_does_not_request_a_tool():
    state = {
        "messages": [
            AIMessage(content="Hello! How can I help you?")
        ]
    }

    result = route_after_agent(state)

    assert result == END