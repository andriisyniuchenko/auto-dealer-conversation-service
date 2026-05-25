# Galaxy Motors — AI Sales Assistant

Auto dealerships lose leads every day to slow response times and missed after-hours inquiries. This project addresses that with an AI sales assistant that engages customers instantly, 24/7 — answering inventory questions, collecting contact details, and booking test drives without any human involvement.

Built on LangGraph, the assistant — named Jessica — streams responses token by token to the browser and integrates directly with a CRM to capture every lead.

This is one half of a two-service system. The other half is [auto_dealer_crm](https://github.com/andriisyniuchenko/auto_dealer_crm) — a separate CRM service that stores leads, sales operations, and chat transcripts.

[![CI](https://github.com/andriisyniuchenko/auto-dealer-conversation-service/actions/workflows/ci.yml/badge.svg)](https://github.com/andriisyniuchenko/auto-dealer-conversation-service/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2-orange)
![OpenSearch](https://img.shields.io/badge/OpenSearch-2.13-blue?logo=opensearch)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)

> Galaxy Motors is a fictional dealership.

---

## What it does

The website side is straightforward — browse 60 vehicles, filter by make/model/year/price/condition, view individual vehicle pages, submit a contact form. Standard stuff.

The interesting part is the chat assistant. A customer opens the chat, asks about inventory ("do you have any used SUVs under $30k?"), Jessica searches the actual database and responds with real results. When the customer shows interest in a specific vehicle, the conversation shifts: Jessica collects their name and phone number, submits a lead to the CRM, and asks if they'd like to schedule a test drive. If they do — she books it. The whole thing streams token by token so it feels instant.

---

## How the AI works

The first version of this was a single large system prompt that told the LLM to collect contact details, submit the lead, ask about a test drive, and book it — all through conversation. It worked most of the time. But "most of the time" isn't good enough when you're capturing sales leads: the LLM would occasionally skip a step, forget to ask for a phone number, or hallucinate a successful lead submission. Debugging it meant reading LLM outputs, not code.

The current version moves all business logic out of the prompt and into a LangGraph graph with deterministic routing. The LLM is only responsible for **conversation** — answering questions about inventory, deciding when the customer is ready to move forward. Everything else (collecting a name, parsing a phone number, booking an appointment) runs as ordinary Python code that behaves the same way every time.

The graph looks like this:

```
Customer message
       │
       ▼
_route_entry()  ←  reads State, decides what happens next
       │
       ├── "__greet__" signal?          → greet node (hardcoded welcome message)
       │
       ├── collecting contact info?
       │     ├── asked for name, waiting → extract_name  (focused LLM call)
       │     ├── asked for phone, waiting → extract_phone (focused LLM call)
       │     └── have both → submit_lead → ask_test_drive
       │
       ├── test drive flow?
       │     ├── asked, waiting for answer → detect_test_drive (keyword match, LLM fallback)
       │     ├── yes → ask_datetime → extract_datetime → book_appointment → farewell
       │     └── no  → farewell
       │
       └── none of the above → agent  (conversational LLM with tools)
                                  │
                                  ├── search_vehicles tool → OpenSearch → response
                                  └── express_interest tool → triggers contact collection
```

The split is intentional: conversational behavior stays in the LLM, business logic runs as deterministic code. The LLM that handles free conversation never sees the contact collection prompts. The extraction LLMs that parse a name or phone number only receive two messages — the instruction and the customer's reply. No chat history, no bloat.

### Agent tools

| Tool | What it does |
|---|---|
| `search_vehicles` | Embeds the query, runs hybrid search (semantic + keyword) against OpenSearch, returns matching vehicles |
| `express_interest` | Called by the LLM when the customer clearly wants to move forward with a vehicle — triggers the contact collection flow |

### State

Every conversation has a persistent `State` object that tracks where things are:

```python
class State(MessagesState):
    customer_first_name: str | None
    customer_last_name: str | None
    customer_phone: str | None
    customer_interest: str | None
    lead_submitted: bool
    crm_lead_id: int | None
    asked_for_name: bool
    asked_for_phone: bool
    test_drive_asked: bool
    wants_test_drive: bool | None  # True / False / None (unanswered)
    asked_for_datetime: bool
    appointment_at: str | None
    appointment_booked: bool
    chat_complete: bool
```

This state is persisted in the LangGraph checkpointer (PostgreSQL in production, in-memory for tests). Each session is identified by a UUID that acts as the `thread_id`.

### Why this architecture

The main tradeoff is complexity upfront — a graph with 14 nodes and routing functions is more code than a single prompt. But it pays off: the contact collection flow always runs the same way regardless of what the LLM decides to say, lead submissions don't get skipped, and when something breaks you can see exactly which node failed and with what state. Extraction LLM calls are also cheap — 2 messages instead of the full conversation history — which is where most of the token savings come from.

---

## Cost

These are estimates based on a realistic dealership conversation: around 10 customer messages, 2–3 agent LLM calls with full conversation history, and 4 focused extraction calls (name, phone, test-drive intent, datetime) with 2 messages each. That works out to roughly 3M input + 0.5M output tokens per 1,000 conversations. Actual usage will vary depending on how long customers chat and how many clarification rounds are needed.

Estimated per **1,000 conversations/month**:

| Model | Provider | Cost |
|---|---|---|
| Gemini 3.1 Flash-Lite | Google | ~$1.50 |
| Gemini 3 Flash | Google | ~$3.00 |
| GPT-5.4 mini | OpenAI | ~$4.50 |
| Claude Haiku 4.5 | Anthropic | ~$5.50 |
| Gemini 3.1 Pro | Google | ~$12.00 |
| GPT-5.4 | OpenAI | ~$15.00 |
| Claude Sonnet 4.6 | Anthropic | ~$16.50 |
| Claude Opus 4.7 | Anthropic | ~$27.50 |
| GPT-5.5 | OpenAI | ~$30.00 |

The LLM provider and model are configured via env vars — no code changes needed to switch.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| AI Agent | LangGraph 1.2, LangChain 1.3 |
| LLM | Configurable via `LLM_PROVIDER` / `LLM_MODEL` — supports OpenAI, Anthropic, Google, Groq, and any provider available through LangChain `init_chat_model()` |
| Embeddings | Ollama + nomic-embed-text (local, 768-dim) |
| Vector Search | OpenSearch 2.13 — KNN + BM25 hybrid pipeline |
| Streaming | Server-Sent Events (SSE) |
| Database | PostgreSQL 15, SQLAlchemy 2.0 async, asyncpg |
| Migrations | Alembic |
| Templating | Jinja2 + Bootstrap 5.3 |
| HTTP client | httpx (async, for CRM calls) |
| Infrastructure | Docker, docker-compose |
| Observability | LangSmith (optional) |
| Config | Pydantic Settings |

---

## Architecture: two services

```
Customer Browser
      │
      ├── GET /inventory, /search, /vehicle/{id}  →  FastAPI  →  PostgreSQL
      │
      ├── POST /contact (lead form)               →  FastAPI  →  CRM API
      │
      └── Chat (SSE)
            ├── POST /api/chat/session            →  returns UUID
            ├── POST /api/chat/message            →  LangGraph → OpenSearch → SSE stream
            └── on lead collected                 →  CRM API  →  save transcript
```

Service-to-service calls use a shared API key via `X-API-Key` header.

| Service | Repo | Port |
|---|---|---|
| Galaxy Motors (this) | auto-dealer-conversation-service | 8001 |
| CRM | auto_dealer_crm | 8000 |

---

## Project structure

```
auto-dealer-conversation-service/
├── app/
│   ├── main.py                    # FastAPI app + lifespan (builds the graph once at startup)
│   ├── agent/
│   │   ├── state.py               # State definition — all conversation fields
│   │   ├── prompts.py             # System prompt for the conversational agent
│   │   ├── tools.py               # search_vehicles, express_interest
│   │   ├── nodes.py               # All graph nodes — agent, extraction LLMs, CRM calls
│   │   └── graph.py               # Graph assembly — nodes, edges, routing functions
│   ├── api/
│   │   ├── chat.py                # /api/chat/* — session, SSE stream, history
│   │   ├── inventory.py           # Vehicle listing, search, detail pages
│   │   ├── contact.py             # POST /contact — lead form
│   │   ├── dependencies.py        # get_graph() dependency injection
│   │   └── routes.py              # Router aggregator
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── database.py            # Async SQLAlchemy engine + session
│   │   ├── llm.py                 # LLM factory — init_chat_model()
│   │   └── templates.py           # Jinja2 setup
│   ├── services/
│   │   ├── opensearch.py          # Async OpenSearch client + hybrid search
│   │   ├── embeddings.py          # Ollama embeddings singleton
│   │   └── crm.py                 # httpx CRM client — leads, appointments, transcripts
│   ├── models/
│   │   └── vehicle.py             # Vehicle ORM model
│   ├── schemas/
│   │   ├── chat.py                # Chat API schemas
│   │   └── lead.py                # Lead form schema
│   ├── static/
│   │   ├── css/                   # Site and chat widget styles
│   │   ├── js/filters.js          # Dynamic filter dropdowns
│   │   └── js/chat.js             # Chat widget — SSE client, session management
│   └── data/
│       └── inventory.json         # 60 vehicles source data
├── scripts/
│   └── seed.py                    # Seeds PostgreSQL + OpenSearch
├── tests/
│   ├── conftest.py                # Fixtures: async SQLite, test client
│   ├── test_inventory.py          # Route + filter tests
│   └── test_contact.py            # Lead form tests
├── .github/workflows/ci.yml
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Getting started

### Requirements

- Docker and docker-compose
- [Ollama](https://ollama.com) running locally with `nomic-embed-text` pulled:
  ```bash
  ollama pull nomic-embed-text
  ```
- An LLM API key — OpenAI, Anthropic, Google, or Groq
- The [CRM service](https://github.com/andriisyniuchenko/auto_dealer_crm) running on port 8000

### Setup

```bash
cp .env.example .env
# edit .env with your keys
```

Key variables:

```env
LLM_PROVIDER=openai          # openai | anthropic | google_genai | groq | ...
LLM_MODEL=gpt-5.4-mini       # any model supported by LangChain init_chat_model()
# set the key for whichever provider you use:
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
# GOOGLE_API_KEY=...
# GROQ_API_KEY=...

OLLAMA_BASE_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text

DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/web_db
OPENSEARCH_URL=http://localhost:9200

CRM_API_URL=http://host.docker.internal:8000
CRM_API_KEY=your-shared-secret
```

### Run

```bash
make demo
```

This starts PostgreSQL and OpenSearch, runs migrations, seeds the vehicle inventory, sets up the OpenSearch hybrid search pipeline, and starts the app. Available at `http://localhost:8001`.

### Other Makefile commands

```bash
make up                         # Start all services
make down                       # Stop and remove volumes
make build                      # Rebuild Docker images
make logs                       # Stream container logs
make migrate                    # Run Alembic migrations
make migration msg="add table"  # Generate new migration
make freeze                     # Update requirements.txt
```

---

## Testing

```bash
pytest tests/ -v
```

52 tests total, split into two areas:

- **Agent logic** (37 tests) — routing functions and deterministic nodes. Covers every state transition in the graph: all `_route_entry` branches, post-tool routing, node outputs, keyword detection. No LLM calls, no external services — runs in under a second.
- **API and inventory** (15 tests) — route responses, filters, 404 handling, lead form validation. Uses in-memory SQLite.

CI runs on every push via GitHub Actions.

---

## Database schema

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
| features | Text | Comma-separated feature list |
| condition | String | new / used |

---

## API routes

### Website

| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage with filters |
| GET | `/search` | Search results |
| GET | `/inventory/new` | New vehicles |
| GET | `/inventory/used` | Used vehicles |
| GET | `/vehicle/{id}` | Vehicle detail page |
| POST | `/contact` | Lead form → CRM |
| GET | `/health` | Health check |

### Chat API

| Method | Route | Description |
|---|---|---|
| POST | `/api/chat/session` | Create a new session, returns UUID |
| POST | `/api/chat/message` | Send a message, returns SSE stream |
| GET | `/api/chat/history/{session_id}` | Full conversation history |

---

## Infrastructure

| Container | Image | Port | Purpose |
|---|---|---|---|
| `web` | Built from Dockerfile | 8001 | FastAPI + LangGraph agent |
| `postgres` | postgres:15 | 5433 | Relational database |
| `opensearch` | opensearchproject/opensearch:2.13.0 | 9200 | Vector + hybrid search |

Ollama runs on the host machine (not in Docker).

---

## A few implementation details worth noting

**Hybrid search** — OpenSearch runs both KNN (semantic vector similarity) and BM25 (keyword) in parallel, then normalizes and combines scores with a 40/60 weighting. 60% keyword works better here because customers search by exact brand and model names, not vague descriptions.

**SSE streaming** — the agent node streams tokens via `on_chat_model_stream` events. Deterministic nodes (greet, ask_name, etc.) emit their full message on `on_chain_end`. The frontend receives both the same way.

**Datetime extraction** — when a customer says "tomorrow at 2pm", the extraction LLM receives today's and tomorrow's actual dates in the prompt and is required to return a proper ISO 8601 datetime. The result is validated by Pydantic (`appointment_at: datetime`) and localized to Pacific Time before being sent to the CRM.

**Lazy singletons** — LLM instances and the ToolNode are initialized on first request, not at import time. The compiled graph is built once during FastAPI lifespan and injected via `Depends(get_graph)`.