import json
import time
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from pydantic import BaseModel, Field

from graph import build_graph
from logging_config import configure_logging

logger = configure_logging()

SYSTEM_PROMPT = """You are a helpful AI assistant.
Use available tools only when they are needed.
For directory requests, use the list_files tool.
For current weather requests, use the get_weather tool.
For every public factual question that is not a greeting or an internal-document question,
use the web_search tool before answering. This includes questions about people,
organizations, events, products, facts, and public information.
Prefer official, primary, government, university, or well-established reference sources.
For webpage reading or summarization requests with a URL, use the scrape_url tool.
For questions about internal documents, policies, or the knowledge base, use rag_search.
Use standard Markdown only when useful. Do not escape standard Markdown characters
such as **, [], (), or | unless they must be displayed literally. Do not use HTML tags.
Never claim that you used a tool when you did not. Never invent a source URL."""

TOOL_TITLES = {
    "list_files": "Filesystem lookup",
    "get_weather": "Weather lookup",
    "web_search": "Web search",
    "rag_search": "Knowledge-base retrieval",
    "scrape_url": "Webpage extraction",
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


app = FastAPI(title="VCTI Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def parse_tool_result(content: Any) -> Any:
    """Convert an MCP ToolMessage payload into JSON when the tool returned JSON."""
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        joined = "\n".join(text_parts)
        if joined:
            return parse_tool_result(joined)
    return content


def text_from_chunk(content: Any) -> str:
    """Extract displayable text from a streamed LangChain message chunk."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return ""


def extract_sources(tool_name: str, result: Any) -> list[dict[str, str]]:
    """Expose only URLs returned by tools; never ask the model to invent citations."""
    if not isinstance(result, dict):
        return []

    if tool_name == "web_search":
        return [
            {"title": item.get("title", "Search result"), "url": item["url"]}
            for item in result.get("results", [])
            if isinstance(item, dict) and isinstance(item.get("url"), str)
            and item["url"].startswith(("https://", "http://"))
        ]

    if tool_name == "scrape_url":
        url = result.get("url")
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            return [{"title": str(result.get("title", "Read webpage")), "url": url}]

    return []


def unique_sources(sources: list[dict[str, str]]) -> list[dict[str, str]]:
    seen_urls: set[str] = set()
    return [
        source for source in sources
        if not (source["url"] in seen_urls or seen_urls.add(source["url"]))
    ]


async def stream_agent(message: str) -> AsyncIterator[str]:
    """Run one graph turn and send browser-friendly trace events as SSE."""
    tool_started: dict[str, float] = {}
    tool_seen = False
    assistant_text = ""
    assistant_streamed = False
    sources: list[dict[str, str]] = []

    yield sse(
        "trace",
        {
            "id": "analysis",
            "title": "Analyzing request",
            "status": "analyzing",
            "reason": "The agent is deciding whether a tool is required.",
        },
    )

    inputs = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]
    }

    try:
        graph = await build_graph()
        async for part in graph.astream(
            inputs,
            stream_mode=["updates", "messages"],
            version="v2",
        ):
            if part["type"] == "messages":
                chunk, metadata = part["data"]
                is_agent_chunk = metadata.get("langgraph_node") == "agent"
                is_tool_call_chunk = bool(
                    isinstance(chunk, AIMessageChunk) and chunk.tool_call_chunks
                )
                token_text = text_from_chunk(getattr(chunk, "content", ""))
                if is_agent_chunk and token_text and not is_tool_call_chunk:
                    assistant_streamed = True
                    yield sse("assistant_delta", {"text": token_text})
                continue

            if part["type"] != "updates":
                continue

            update = part["data"]
            for node_name, node_update in update.items():
                for graph_message in node_update.get("messages", []):
                    if node_name == "agent" and isinstance(graph_message, AIMessage):
                        calls = graph_message.tool_calls or []
                        if calls:
                            tool_seen = True
                            for call in calls:
                                tool_id = call.get("id", f"tool-{time.monotonic_ns()}")
                                tool_started[tool_id] = time.perf_counter()
                                tool_name = call.get("name", "unknown_tool")
                                yield sse(
                                    "trace",
                                    {
                                        "id": tool_id,
                                        "title": TOOL_TITLES.get(tool_name, tool_name),
                                        "tool": tool_name,
                                        "status": "pending",
                                        "reason": "Selected by the agent for this request.",
                                        "args": call.get("args", {}),
                                    },
                                )
                        elif graph_message.content:
                            assistant_text = str(graph_message.content)

                    if node_name == "tools" and isinstance(graph_message, ToolMessage):
                        tool_id = graph_message.tool_call_id
                        result = parse_tool_result(graph_message.content)
                        failure = isinstance(result, dict) and result.get("success") is False
                        latency_start = tool_started.get(tool_id)
                        latency = None
                        if latency_start is not None:
                            latency = f"{(time.perf_counter() - latency_start) * 1000:.0f} ms"
                        update_data: dict[str, Any] = {
                            "id": tool_id,
                            "status": "error" if failure else "success",
                            "latency": latency,
                        }
                        if failure:
                            update_data["error"] = str(result.get("error", "Tool request failed."))
                        else:
                            update_data["result"] = result
                            sources.extend(extract_sources(graph_message.name, result))
                        yield sse("trace", update_data)

        yield sse("trace", {"id": "analysis", "status": "success"})

        if not tool_seen:
            yield sse(
                "trace",
                {
                    "id": "no-tool",
                    "title": "No tool required",
                    "status": "no_tool",
                    "reason": "The request can be answered directly.",
                },
            )

        if assistant_streamed:
            yield sse("assistant_done", {"sources": unique_sources(sources)})
        else:
            yield sse(
                "assistant",
                {
                    "text": assistant_text or "The agent did not return a response.",
                    "sources": unique_sources(sources),
                },
            )
    except Exception as error:
        logger.exception("API agent request failed")
        error_text = f"I could not complete that request: {error}"
        yield sse(
            "trace",
            {
                "id": "agent-error",
                "title": "Agent request failed",
                "status": "error",
                "reason": "The request could not be completed.",
                "error": str(error),
            },
        )
        yield sse("assistant", {"text": error_text})


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    message = request.message.strip()
    logger.info("Web chat request received")
    return StreamingResponse(
        stream_agent(message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
