from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import trafilatura

import httpx
from mcp.server.fastmcp import FastMCP

from config import DATA_DIR, PROJECT_ROOT, TAVILY_API_KEY
from logging_config import configure_logging
from rag.retriever import search_knowledge_base

mcp = FastMCP("VCTI Assignment MCP Tools")
logger = configure_logging()

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def log_tool(function):
    """Log MCP tool arguments and completion without logging credentials."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        safe_arguments = {
            key: "[REDACTED]"
            if any(word in key.lower() for word in ("key", "token", "secret", "password"))
            else value
            for key, value in kwargs.items()
        }
        logger.info(
            "Tool started: %s | arguments=%s",
            function.__name__,
            safe_arguments,
        )

        try:
            result = function(*args, **kwargs)
            success = result.get("success") if isinstance(result, dict) else None
            logger.info(
                "Tool completed: %s | success=%s",
                function.__name__,
                success,
            )
            return result
        except Exception:
            logger.exception("Tool failed unexpectedly: %s", function.__name__)
            raise

    return wrapper


def get_safe_directory(directory: str) -> Path:
    """Resolve a path and ensure it stays inside ./data."""
    requested_path = Path(directory)

    if requested_path.is_absolute():
        resolved_path = requested_path.resolve()
    else:
        resolved_path = (PROJECT_ROOT / requested_path).resolve()

    try:
        resolved_path.relative_to(DATA_DIR)
    except ValueError as error:
        raise ValueError("Access is allowed only inside the ./data directory.") from error

    return resolved_path


@mcp.tool()
@log_tool
def list_files(directory: str) -> dict:
    """
    List files and subdirectories inside a safe directory.

    Args:
        directory: A path inside ./data, for example './data/documents'.
    """
    try:
        safe_directory = get_safe_directory(directory)

        if not safe_directory.exists():
            return {
                "success": False,
                "error": f"Directory does not exist: {directory}",
            }

        if not safe_directory.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {directory}",
            }

        items = [
            {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
            }
            for item in sorted(safe_directory.iterdir(), key=lambda path: path.name.lower())
        ]

        return {
            "success": True,
            "directory": str(safe_directory.relative_to(PROJECT_ROOT)),
            "items": items,
        }

    except ValueError as error:
        return {"success": False, "error": str(error)}
    except OSError as error:
        return {"success": False, "error": f"Could not read directory: {error}"}


@mcp.tool()
@log_tool
def get_weather(location: str) -> dict:
    """
    Get current weather for any city or location.

    Args:
        location: A city or location name, for example 'Bangalore' or 'Kanpur'.
    """
    try:
        with httpx.Client(
            timeout=10.0,
            trust_env=False,
            headers={"User-Agent": "vcti-langgraph-mcp-assignment/1.0"},
        ) as client:
            # Generic location search: accepts free-form city/location text.
            geocoding_response = client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": location,
                    "format": "jsonv2",
                    "limit": 1,
                },
            )
            geocoding_response.raise_for_status()

            results = geocoding_response.json()
            if not results:
                return {
                    "success": False,
                    "error": f"Could not find a location named '{location}'.",
                }

            place = results[0]

            weather_response = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["lat"],
                    "longitude": place["lon"],
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "weather_code,wind_speed_10m"
                    ),
                    "temperature_unit": "celsius",
                    "wind_speed_unit": "kmh",
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()

        current = weather_response.json()["current"]

        return {
            "success": True,
            "location": place["display_name"],
            "temperature_c": current["temperature_2m"],
            "condition": WEATHER_CODES.get(
                int(current["weather_code"]),
                "Unknown condition",
            ),
            "humidity_percent": current["relative_humidity_2m"],
            "wind_speed_kmh": current["wind_speed_10m"],
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "The weather service timed out. Please try again.",
        }
    except httpx.HTTPError:
        return {
            "success": False,
            "error": "The weather service could not be reached.",
        }
    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "error": "The weather service returned an unexpected response.",
        }
@mcp.tool()
@log_tool
def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search the web and return structured results.

    Args:
        query: Search query, for example 'latest LangGraph tutorials'.
        max_results: Number of results to return, from 1 to 10.
    """
    if not TAVILY_API_KEY:
        return {
            "success": False,
            "error": "TAVILY_API_KEY is missing from the .env file.",
        }

    if not query.strip():
        return {
            "success": False,
            "error": "Search query cannot be empty.",
        }

    result_limit = max(1, min(max_results, 10))

    try:
        with httpx.Client(timeout=20.0, trust_env=False) as client:
            response = client.post(
                "https://api.tavily.com/search",
                headers={
                    "Authorization": f"Bearer {TAVILY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "search_depth": "basic",
                    "max_results": result_limit,
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()

        search_data = response.json()

        results = [
            {
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score"),
            }
            for item in search_data.get("results", [])
        ]

        return {
            "success": True,
            "query": query,
            "results": results,
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "The web-search service timed out. Please try again.",
        }
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 401:
            return {
                "success": False,
                "error": "The Tavily API key is invalid or unauthorized.",
            }

        if error.response.status_code == 429:
            return {
                "success": False,
                "error": "Web-search rate limit reached. Please try again later.",
            }

        return {
            "success": False,
            "error": "The web-search service returned an error.",
        }
    except httpx.HTTPError:
        return {
            "success": False,
            "error": "The web-search service could not be reached.",
        }
@mcp.tool()
@log_tool
def scrape_url(url: str) -> dict:
    """
    Extract the title and main readable content from a webpage.

    Args:
        url: A valid HTTP or HTTPS URL.
    """
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return {
            "success": False,
            "error": "Please provide a valid HTTP or HTTPS URL.",
        }

    if parsed_url.hostname in {"localhost", "127.0.0.1", "::1"}:
        return {
            "success": False,
            "error": "Local URLs are not allowed.",
        }

    try:
        with httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            trust_env=False,
            headers={
                "User-Agent": "VCTI-LangGraph-MCP-Assignment/1.0",
            },
        ) as client:
            response = client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return {
                "success": False,
                "error": "The URL did not return an HTML webpage.",
            }

        html = response.text
        if not html.strip():
            return {
                "success": False,
                "error": "The webpage returned no content.",
            }

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else "Untitled page"

        # Extract only the useful article/main-page content.
        content = trafilatura.extract(
            html,
            url=str(response.url),
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )

        # Fallback for pages where article extraction finds nothing.
        if not content:
            for unwanted_tag in soup(
                ["script", "style", "nav", "footer", "header", "aside", "noscript"]
            ):
                unwanted_tag.decompose()

            content = soup.get_text(separator=" ", strip=True)

        if not content:
            return {
                "success": False,
                "error": "No readable content was found on this webpage.",
            }

        maximum_length = 12_000
        is_truncated = len(content) > maximum_length

        return {
            "success": True,
            "url": str(response.url),
            "title": title,
            "content": content[:maximum_length],
            "metadata": {
                "content_truncated": is_truncated,
            },
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "The webpage request timed out.",
        }
    except httpx.HTTPStatusError as error:
        return {
            "success": False,
            "error": f"The webpage returned HTTP status {error.response.status_code}.",
        }
    except httpx.HTTPError:
        return {
            "success": False,
            "error": "The webpage could not be reached.",
        }


@mcp.tool()
@log_tool
def rag_search(query: str, max_results: int = 3) -> dict:
    """
    Search internal documents in the local knowledge base.

    Args:
        query: A question about internal policies or indexed documents.
        max_results: Number of relevant chunks to retrieve, from 1 to 5.
    """
    return search_knowledge_base(query, max_results)


if __name__ == "__main__":
    mcp.run(transport="stdio")
