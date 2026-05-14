# 🚗 Galaxy Motors — AI-Powered Auto Dealer Web App

A full-stack web application for a fictional auto dealership with an integrated **AI chat assistant** built on LangGraph and RAG. Part of a two-service microservice system — this service handles the customer-facing website and AI chat, while a separate CRM ([auto_dealer_crm](https://github.com/andriisyniuchenko/auto_dealer_crm)) manages leads and sales operations.

[![CI](https://github.com/andriisyniuchenko/auto-dealer-conversation-service/actions/workflows/ci.yml/badge.svg)](https://github.com/andriisyniuchenko/auto-dealer-conversation-service/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-orange)
![OpenSearch](https://img.shields.io/badge/OpenSearch-2.13-blue?logo=opensearch)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)

> **Demo project for portfolio purposes only. Not a real dealership.**

---

## ✨ Features

- 🔍 Browse and filter 60 vehicles by condition, make, model, year, mileage, and price
- 🚘 Individual vehicle pages with specs, features, and photos
- 📋 Lead form — forwards inquiries to the CRM via HTTP
- 🤖 **AI chat assistant (Jessica)** — RAG-powered, streams responses token by token via SSE
- 💬 Chat transcript automatically saved to CRM when a lead is collected
- 🔗 Full microservice integration with auto_dealer_crm

---

## 🤖 AI Chat Assistant — How It Works

Jessica is a ReAct-style LangGraph agent that uses **RAG (Retrieval-Augmented Generation)** to answer questions about the vehicle inventory.

```
Customer: "Do you have a used Toyota under $20k?"
        ↓
LangGraph ReAct Agent (Jessica)
        ↓
search_vehicles("used Toyota under $20k")
        ↓
Ollama (nomic-embed-text) — embed query into 768-dim vector
        ↓
OpenSearch — hybrid search (KNN vector + BM25 keyword)
        ↓
Top 5 matching vehicles returned as context
        ↓
Groq (llama-3.3-70b-versatile) — generates natural language response
        ↓
SSE stream → token by token to the browser
        ↓
When customer leaves contact details → submit_lead tool → CRM
        ↓
Chat transcript saved to CRM (linked to the lead)
```

### Agent Tools

| Tool | Description |
|---|---|
| `search_vehicles` | Hybrid semantic + keyword search across inventory |
| `submit_lead` | Sends customer contact details to CRM |

### Key Design Decisions

- **LangGraph `MessagesState`** — conversation history with structured state (`lead_submitted`, `crm_lead_id`, customer fields)
- **`MemorySaver` checkpointer** — per-session memory via `thread_id = session_id`
- **Hybrid search** — KNN (semantic) + BM25 (keyword) with `normalization-processor` pipeline. Weights: 40% vector, 60% keyword — better for brand/model queries
- **SSE streaming** — `graph.astream_events()` filtered on `on_chat_model_stream`
- **Dependency injection** — graph built once at startup via FastAPI `lifespan`, injected via `Depends(get_graph)`
- **Lazy singletons** — LLM and ToolNode initialized on first request, not at import time

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| AI Agent | LangGraph 1.2, LangChain 1.3 |
| LLM | Groq (llama-3.3-70b-versatile), swappable via `LLM_PROVIDER` / `LLM_MODEL` env vars |
| Embeddings | Ollama + nomic-embed-text (local, 768-dim) |
| Vector Search | OpenSearch 2.13 — KNN + hybrid search pipeline |
| Streaming | Server-Sent Events (SSE) via `StreamingResponse` |
| Async | SQLAlchemy 2.0 async, asyncpg, httpx |
| Templating | Jinja2 + Bootstrap 5.3 |
| Database | PostgreSQL 15 |
| Migrations | Alembic |
| Infrastructure | Docker, docker-compose |
| Observability | LangSmith (optional) |
| Configuration | Pydantic Settings |

---

## 🏛️ Microservice Architecture

```
Customer Browser
      │
      ├── GET /inventory, /search, /vehicle/{id}  →  FastAPI (this service)  →  PostgreSQL
      │
      ├── POST /contact (lead form)  →  FastAPI  →  CRM API  →  CRM PostgreSQL
      │
      └── WebSocket-like chat (SSE)
            │
            ├── POST /api/chat/session        → create UUID session
            ├── POST /api/chat/message        → LangGraph agent → OpenSearch + Groq → SSE stream
            └── (on lead_submitted)           → CRM API → save chat transcript
```

**Service-to-service authentication** uses a shared API key via `X-API-Key` header.

| Service | Repo | Port | Role |
|---|---|---|---|
| Galaxy Motors (this) | auto-dealer-conversation-service | 8001 | Customer website + AI chat |
| Auto Dealer CRM | auto_dealer_crm | 8000 | Leads, sales ops, chat history |

---

## 📁 Project Structure

```
auto-dealer-conversation-service/
├── app/
│   ├── main.py                    # FastAPI app, lifespan (builds LangGraph)
│   ├── agent/
│   │   ├── state.py               # LangGraph State (MessagesState + lead fields)
│   │   ├── prompts.py             # System prompt (SYSTEM_MESSAGE constant)
│   │   ├── tools.py               # search_vehicles, submit_lead tools
│   │   ├── nodes.py               # agent_node, tool_node, track_lead_node
│   │   └── graph.py               # StateGraph — build_graph()
│   ├── api/
│   │   ├── routes.py              # Router aggregator
│   │   ├── dependencies.py        # get_graph() DI
│   │   ├── chat.py                # /api/chat/* — session, SSE message, history
│   │   ├── inventory.py           # Vehicle listing, search, detail routes
│   │   ├── contact.py             # POST /contact — lead form
│   │   └── pages.py               # Static pages
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── database.py            # Async SQLAlchemy engine & session
│   │   ├── llm.py                 # LLM factory — init_chat_model()
│   │   └── templates.py           # Jinja2 environment
│   ├── services/
│   │   ├── opensearch.py          # AsyncOpenSearch client + hybrid search
│   │   ├── embeddings.py          # OllamaEmbeddings singleton
│   │   └── crm.py                 # httpx CRM client (leads + chat sessions)
│   ├── models/
│   │   └── vehicle.py             # Vehicle ORM model
│   ├── schemas/
│   │   ├── chat.py                # Chat API Pydantic schemas
│   │   └── lead.py                # Lead form schema
│   ├── static/
│   │   ├── css/style.css
│   │   ├── css/chat.css           # Chat widget styles
│   │   ├── js/filters.js          # Dynamic dependent dropdowns
│   │   ├── js/chat.js             # Chat widget — SSE client, session management
│   │   └── img/
│   └── data/
│       └── inventory.json         # 60 vehicles source data
├── scripts/
│   └── seed.py                    # Seeds PostgreSQL + OpenSearch (hybrid pipeline)
├── tests/
│   ├── conftest.py                # Fixtures: async SQLite DB, test client
│   ├── test_inventory.py          # Route and filter tests
│   └── test_contact.py            # Lead form tests
├── .github/workflows/ci.yml       # GitHub Actions CI
├── alembic/                       # Database migrations
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## 🗄️ Database Schema

### `vehicles`
| Column | Type | Description |
|---|---|---|
| id | String (PK) | Unique vehicle ID |
| make | String | Manufacturer |
| model | String | Model name |
| trim | String (nullable) | Trim level |
| year | Integer | Model year |
| type | String | Body type |
| transmission | String | automatic / manual |
| mileage | Integer | Odometer in miles |
| price | Float | Asking price USD |
| color | String | Exterior color |
| engine | String | Engine description |
| origin | String | japanese / american / european / korean |
| features | Text | Comma-separated features |
| condition | String | new / used |

---

## 🌐 API Routes

### Website
| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage with filters |
| GET | `/search` | Search results page |
| GET | `/inventory/new` | New vehicles listing |
| GET | `/inventory/used` | Used vehicles listing |
| GET | `/vehicle/{id}` | Vehicle detail page |
| POST | `/contact` | Lead form → CRM |
| GET | `/health` | Health check |

### Chat API
| Method | Route | Description |
|---|---|---|
| POST | `/api/chat/session` | Create new chat session |
| POST | `/api/chat/message` | Send message → SSE stream |
| GET | `/api/chat/history/{session_id}` | Get conversation history |

---

## 🏗️ Infrastructure

| Service | Image | Port | Purpose |
|---|---|---|---|
| `web` | Built from Dockerfile | 8001 | FastAPI + LangGraph agent |
| `postgres` | postgres:15 | 5433 | Relational database |
| `opensearch` | opensearchproject/opensearch:2.13.0 | 9200 | Vector + hybrid search |

Ollama runs on the host machine (not in Docker). Set `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env`.

---

## 🚀 Getting Started

### Requirements

- Docker & docker-compose
- [Ollama](https://ollama.com) installed and running on host
- `nomic-embed-text` model pulled: `ollama pull nomic-embed-text`
- Groq API key (free): [console.groq.com](https://console.groq.com)

### Environment Setup

```bash
cp .env.example .env
```

Key variables:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/web_db
OPENSEARCH_URL=http://localhost:9200
OLLAMA_BASE_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_groq_api_key
CRM_API_URL=http://localhost:8000
CRM_API_KEY=your-secret-api-key
```

> `CRM_API_KEY` must match the key configured in the CRM service.

### Run with Docker

```bash
make demo
```

This command: starts PostgreSQL + OpenSearch → runs migrations → seeds inventory + OpenSearch hybrid pipeline → starts the web service.

App available at: `http://localhost:8001`

### Makefile Commands

```bash
make up                         # Start all services
make down                       # Stop and remove volumes
make build                      # Rebuild Docker images
make demo                       # Full setup: DBs → migrate → seed → start
make migrate                    # Run Alembic migrations
make migration msg="add table"  # Generate new migration
make logs                       # Stream container logs
make freeze                     # Update requirements.txt
```

---

## 🧪 Testing

```bash
pytest tests/ -v
```

15 tests covering inventory routes, filters, 404 handling, and lead form validation. Tests use an in-memory SQLite database — no external services required.

CI runs on every push via GitHub Actions.

---

## 🔑 Technical Notes

- **RAG**: Vehicle inventory indexed in OpenSearch as 768-dim vectors. On each query, the agent embeds the question with Ollama and runs a hybrid search (KNN + BM25) to retrieve relevant vehicles as LLM context.
- **Hybrid search**: `normalization-processor` pipeline normalizes scores from both KNN and BM25, then combines with arithmetic mean (40% / 60% weights). Created automatically during `make demo`.
- **SSE**: `graph.astream_events()` with `version="v2"`, filtered on `on_chat_model_stream`. Yields `{"token": "..."}` chunks and `{"event": "lead_submitted"}` on completion.
- **State**: `lead_submitted`, `crm_lead_id`, and customer fields stored in `State(MessagesState)`. `track_lead_node` reads `tool_calls` from AIMessage to extract CRM lead ID after successful submission.
- **Async**: All routes `async def`. SQLAlchemy async engine + asyncpg. httpx for CRM calls. OllamaEmbeddings async via `aembed_query`.
- **Security**: Jinja2 autoescape enabled. CRM key in env only. Agent system prompt blocks internal detail disclosure.
- **LLM swappable**: Change `LLM_PROVIDER` / `LLM_MODEL` in `.env` — uses `init_chat_model()` from LangChain.