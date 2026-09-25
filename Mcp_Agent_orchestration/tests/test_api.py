import json

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

import api


class FakeGraph:
    async def astream(self, inputs, stream_mode, version):
        # Agent selects web_search.
        yield {
            "type": "updates",
            "data": {
                "agent": {
                    "messages": [
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "web_search",
                                    "args": {"query": "Virender Sehwag"},
                                    "id": "search-1",
                                    "type": "tool_call",
                                }
                            ],
                        )
                    ]
                }
            },
        }

        # Fake successful response from the web_search tool.
        yield {
            "type": "updates",
            "data": {
                "tools": {
                    "messages": [
                        ToolMessage(
                            name="web_search",
                            tool_call_id="search-1",
                            content=json.dumps(
                                {
                                    "success": True,
                                    "results": [
                                        {
                                            "title": "Example trusted source",
                                            "url": "https://example.com/source",
                                            "snippet": "Example search result.",
                                            "score": 0.95,
                                        }
                                    ],
                                }
                            ),
                        )
                    ]
                }
            },
        }

        # Fake assistant response tokens.
        yield {
            "type": "messages",
            "data": (
                AIMessageChunk(content="Virender "),
                {"langgraph_node": "agent"},
            ),
        }

        yield {
            "type": "messages",
            "data": (
                AIMessageChunk(content="Sehwag is a former Indian cricketer."),
                {"langgraph_node": "agent"},
            ),
        }

        # Final completed agent message.
        yield {
            "type": "updates",
            "data": {
                "agent": {
                    "messages": [
                        AIMessage(
                            content="Virender Sehwag is a former Indian cricketer."
                        )
                    ]
                }
            },
        }


async def fake_build_graph():
    return FakeGraph()


def test_api_streams_tool_trace_answer_and_source(monkeypatch):
    monkeypatch.setattr(api, "build_graph", fake_build_graph)

    client = TestClient(api.app)

    response = client.post(
        "/api/chat",
        json={"message": "Who is Virender Sehwag?"},
    )

    assert response.status_code == 200

    stream = response.text

    assert "event: trace" in stream
    assert '"tool": "web_search"' in stream
    assert '"status": "pending"' in stream
    assert '"status": "success"' in stream

    assert "event: assistant_delta" in stream
    assert "Virender " in stream
    assert "Sehwag is a former Indian cricketer." in stream

    assert "event: assistant_done" in stream
    assert "https://example.com/source" in stream


def test_api_rejects_empty_message():
    client = TestClient(api.app)

    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422