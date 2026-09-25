# MCP Agent Orchestration

A multi-tool AI agent built with **LangGraph** and the **Model Context Protocol (MCP)**. The agent receives a user question, autonomously decides whether it needs a tool (or chain of tools), calls the required MCP tool(s), and streams back a final answer — with a React frontend that shows the agent's reasoning trace live.

## ✨ Features

- 🧠 **LangGraph-based agent** that decides when to call a tool vs. answer directly
- 🔧 **5 MCP tools**: file listing, weather, web search, RAG document search, and URL scraping
- 📚 **RAG pipeline** over local documents using ChromaDB + Hugging Face embeddings
- ⚡ **Streaming responses** via Server-Sent Events (SSE) — token-by-token answers plus a live tool-trace panel
- 🖥️ **React + TypeScript + Vite + Tailwind** frontend with an observability panel for every agent step
- 🔒 Path-restricted filesystem access, blocked localhost scraping, and redacted secrets in logs

## 🏗️ Architecture

```
                 +--------------------+
                 |       START        |
                 +--------------------+
                            |
                            v
                 +--------------------+
                 |     agent node     |
                 |  Groq LLM decides  |
                 |  tool vs. answer   |
                 +--------------------+
                            |
              +-------------+-------------+
              |                           |
      no tool needed              tool call(s) found
              |                           |
              v                           v
        +-----------+           +----------------------+
        |    END    |           |  ToolNode executes    |
        +-----------+           |  one or more MCP tools|
                                 +----------------------+
                                            |
                                            v
                                 +----------------------+
                                 |     agent node        |
                                 | reads tool results and |
                                 |  creates final answer  |
                                 +----------------------+
                                            |
                                            v
                                        +-------+
                                        |  END  |
                                        +-------+
```

- The agent can answer directly when no tool is needed.
- The agent can call a single tool (e.g. `get_weather`).
- The agent can chain tools (e.g. `web_search` → `scrape_url`).
- Tool results are appended to the message state before the final answer is generated.

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| Tool protocol | MCP / FastMCP |
| LLM | Groq (`langchain-groq`) |
| Web search | Tavily |
| Embeddings | Hugging Face SentenceTransformers (local, `all-MiniLM-L6-v2`) |
| Vector store | ChromaDB |
| Backend API | FastAPI + SSE |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Geocoding / Weather | Nominatim (OpenStreetMap) + Open-Meteo (no API key required) |

## 🛠️ The 5 MCP Tools

All tools are defined in `mcp_servers/server.py`.

1. **`list_files(directory)`** — Lists files/folders restricted to the safe `./data` directory (no access outside it).
2. **`get_weather(location)`** — Resolves a location via Nominatim, then fetches current temperature, humidity, wind, and condition from Open-Meteo. Works with any city.
3. **`web_search(query, max_results)`** — Searches the public web via Tavily; returns title, URL, snippet, and relevance score.
4. **`rag_search(query, max_results)`** — Searches internal documents in `data/documents`; returns relevant chunks, source filename, and similarity score.
5. **`scrape_url(url)`** — Reads a public HTTP/HTTPS page and extracts the title and readable main content. Blocks localhost URLs.

## 📚 RAG Pipeline

```
data/documents/  →  rag/ingestion.py (chunking)  →  HF embeddings (local)  →  ChromaDB (chroma_db/)  →  rag_search (chunks + sources + scores)
```

- `rag/embeddings.py` — loads the Hugging Face embedding model
- `rag/ingestion.py` — splits and stores documents in ChromaDB
- `rag/retriever.py` — retrieves relevant chunks for a query

**Example**
> Q: "What is the annual leave policy?"
> Source: `data/documents/employee_policy.txt`
> A: "Employees are entitled to 12 days of annual leave each year."

## 🌐 Backend API

`api.py` exposes:

```
POST /api/chat
```

Streamed via **Server-Sent Events**:

| Event | Purpose |
|---|---|
| `trace` | Agent analysis, tool selection, arguments, pending/success/error status |
| `assistant_delta` | Token-by-token streamed answer |
| `assistant_done` | Completion signal, includes source links |
| `assistant` | Non-streamed fallback (e.g. certain error cases) |

Source links are extracted only from real `web_search` / `scrape_url` results — the LLM is instructed never to invent URLs.

## 🖥️ Frontend

Located in `frontend/`:

- **ChatPanel** — conversation view + example prompt buttons
- **InputBar** — message input and submission
- **MessageBubble** — user/agent messages with clickable source links
- **AgentTracePanel** — live observability panel for the current request
- **ToolStep** — displays a single agent/tool step
- **ToolResultViewer** — expandable raw JSON, RAG sources, and similarity scores
- **Sidebar** — simple conversation sidebar

Shows: streaming text with a pulsing cursor, agent analysis state, selected tool, arguments, pending/success/error/no-tool states, latency, expandable raw output, and clickable sources.

## 📁 Project Structure

```
Mcp_Agent_orchestration/
├── api.py                 # FastAPI app + /api/chat SSE endpoint
├── app.py                 # App entry point
├── config.py               # Configuration / env loading
├── graph.py                # LangGraph agent workflow
├── logging_config.py       # Logging setup (writes to logs/agent.log)
├── mcp_servers/
│   └── server.py            # 5 MCP tool definitions
├── rag/
│   ├── embeddings.py         # HF embedding model loader
│   ├── ingestion.py          # Document chunking + ChromaDB storage
│   └── retriever.py          # Chunk retrieval for RAG
├── data/documents/          # Source documents for RAG
├── frontend/                # React + TypeScript + Vite + Tailwind app
├── tests/                   # Test suite
├── requirements.txt
├── .env.example
└── detail.txt                # Full implementation notes
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js + npm
- API keys: [Groq](https://console.groq.com/) and [Tavily](https://tavily.com/)

### 1. Clone and set up the backend

```bash
git clone https://github.com/Nitesh2417/Mcp_Agent_orchestration.git
cd Mcp_Agent_orchestration

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

> Weather does not require an API key — it uses Nominatim + Open-Meteo.

### 3. Run the backend

```bash
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

### 4. Run the frontend (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open the Vite dev URL, typically:

```
http://localhost:5173
```

## 💬 Example Questions to Try

- "List files in ./data/documents"
- "What is the weather in Bangalore?"
- "What is the annual leave policy?"
- "Read https://example.com and tell me the title."
- "Search official LangGraph documentation for MCP integration."
- "Who is Virender Sehwag? Use official cricket sources."

## 🔐 Error Handling & Safety

- Filesystem tool restricted to `./data` only
- Invalid/localhost URLs rejected by the scraper
- Timeouts handled for weather, search, and scraping calls
- Tavily invalid-key/rate-limit errors handled gracefully
- RAG clearly reports when no relevant documents are found
- Credentials kept in `.env`, excluded via `.gitignore`
- Sensitive log keys (`key`, `token`, `secret`, `password`) are redacted in `logs/agent.log`

## 📝 License

No license specified yet.

## 👤 Author

**Gaurav** — [@Gaurav0234](https://github.com/Gaurav0234)
