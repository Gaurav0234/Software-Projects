# LangGraph MCP Agent Console

Standalone React, TypeScript, Vite, and Tailwind frontend for demonstrating a LangGraph agent that uses MCP tools.

## Run locally

Open two PowerShell terminals from the project root.

In the first terminal, start the FastAPI backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

In the second terminal, start the React frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open the address Vite prints (normally `http://localhost:5173`). `npm.cmd` is used because this machine blocks the PowerShell `npm.ps1` script.

## Demo capabilities

- Filesystem listing, weather, web search, RAG retrieval, and webpage scraping
- Sequential multi-tool trace (`Research + read`)
- No-tool and explicit RAG no-result states
- Expandable raw JSON for each completed tool call
- RAG result source filenames and similarity scores

The UI now connects to the FastAPI endpoint at `/api/chat` through Vite's local proxy. The FastAPI server streams real LangGraph tool-selection and tool-result events using SSE.
