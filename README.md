# Galaxy Motors — Auto Dealer Web Application

A full-stack web application for a fictional auto dealership built with Python and FastAPI. Part of a two-service microservice system — this service handles the customer-facing website, while a separate CRM service ([auto_dealer_crm](https://github.com/andriisyniuchenko/auto_dealer_crm)) manages leads and sales operations.

> **Demo project for portfolio purposes only. Not a real dealership.**

---

## What It Does

- Browse a full inventory of 60 vehicles (30 new 2026 Subaru models, 30 used vehicles)
- Filter by condition, make, year, mileage, and price
- View individual vehicle pages with specs, features, and photos
- Submit a "Request More Information" form — leads are sent to the CRM service via HTTP
- Navigate dealership pages: New Vehicles, Used Vehicles, About Us, Parts & Service

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| Async | SQLAlchemy 2.0 async, asyncpg, httpx |
| Templating | Jinja2, Bootstrap 5.3 |
| Database | PostgreSQL 15, SQLAlchemy 2.0 |
| Migrations | Alembic |
| Vector DB | ChromaDB (for upcoming AI assistant) |
| AI / LLM | Ollama (llama3.2, local) — planned |
| Infrastructure | Docker, docker-compose |
| Configuration | Pydantic Settings, python-dotenv |

---

## Microservice Architecture

This project is one of two services that communicate over HTTP:

```
Customer fills form
        ↓
POST /contact  (this service)
        ↓
httpx.AsyncClient  →  POST /api/v1/leads/public  (CRM service)
        ↓
Lead saved in CRM database with source="website"
```

**Service-to-service authentication** uses a shared API key passed via `X-API-Key` header. The key is stored in `.env` on both sides and never exposed in source code.

| Service | Repo | Port | Role |
|---|---|---|---|
| Galaxy Motors (this) | auto-dealer-conversation-service | 8001 | Customer-facing website |
| Auto Dealer CRM | auto_dealer_crm | 8000 | Internal CRM, leads management |

---

## Project Structure

```
auto-dealer-conversation-service/
├── app/
│   ├── main.py                  # FastAPI app entry point, global exception handler
│   ├── api/
│   │   ├── routes.py            # Router aggregator
│   │   ├── inventory.py         # Vehicle listing, search, detail routes
│   │   ├── contact.py           # POST /contact — lead form handler
│   │   └── pages.py             # Static pages (About, Parts & Service)
│   ├── core/
│   │   ├── config.py            # Environment settings (Pydantic)
│   │   ├── database.py          # Async SQLAlchemy engine & session
│   │   └── templates.py         # Jinja2 template engine setup
│   ├── models/
│   │   ├── vehicle.py           # Vehicle ORM model
│   │   └── chat.py              # ChatSession & ChatMessage ORM models
│   ├── schemas/
│   │   └── lead.py              # Pydantic schema for lead form validation
│   ├── services/
│   │   └── crm.py               # httpx client — sends leads to CRM service
│   ├── templates/
│   │   ├── base.html            # Base layout (topbar, navbar, footer)
│   │   ├── index.html           # Homepage with search & filter
│   │   ├── vehicle_list.html    # New / Used vehicle listing
│   │   ├── vehicle_detail.html  # Vehicle detail page + lead form
│   │   ├── about.html           # About Us page
│   │   └── parts_service.html   # Parts & Service page
│   ├── static/
│   │   ├── css/style.css        # Custom styles
│   │   └── img/
│   │       ├── types/           # Fallback images by body type
│   │       └── models/          # Model-specific images (Subaru lineup)
│   └── data/
│       └── inventory.json       # Source inventory data (60 vehicles)
├── scripts/
│   └── seed.py                  # Seeds PostgreSQL + ChromaDB from inventory.json
├── alembic/                     # Database migrations
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## Database Schema

### `vehicles`
| Column | Type | Description |
|---|---|---|
| id | String (PK) | Unique vehicle ID |
| make | String | Manufacturer (Toyota, Subaru...) |
| model | String | Model name |
| year | Integer | Model year |
| type | String | Body type (sedan, suv, truck...) |
| transmission | String | automatic / manual |
| mileage | Integer | Odometer in miles |
| price | Float | Asking price in USD |
| color | String | Exterior color |
| engine | String | Engine description |
| origin | String | japanese / american / european / korean |
| features | Text | Comma-separated feature list |
| condition | String | new / used |

### `chat_sessions`
| Column | Type | Description |
|---|---|---|
| id | String (PK) | UUID session identifier |
| customer_name | String | Customer's name |
| created_at | DateTime | Session start time |

### `chat_messages`
| Column | Type | Description |
|---|---|---|
| id | String (PK) | UUID message identifier |
| session_id | FK | References chat_sessions.id |
| role | Enum | user / assistant |
| content | Text | Message content |
| created_at | DateTime | Message timestamp |

---

## API Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage — full inventory with filters |
| GET | `/inventory/new` | New vehicles listing |
| GET | `/inventory/used` | Used vehicles listing |
| GET | `/vehicle/{id}` | Individual vehicle detail page |
| POST | `/contact` | Lead form — forwards to CRM service |
| GET | `/about` | About Us page |
| GET | `/parts-service` | Parts & Service page |
| GET | `/health` | Health check |

### Search Filter Parameters (`GET /`)

| Parameter | Example | Description |
|---|---|---|
| `condition` | `new` / `used` | Vehicle condition |
| `year` | `2026` | Exact model year |
| `make` | `Subaru` | Manufacturer |
| `mileage_range` | `under_40000` | Mileage filter |
| `price_range` | `over_60000` | Price filter |

Filter values follow the pattern `under_X` or `over_X` (e.g. `under_30000`, `over_60000`).

---

## Infrastructure

| Service | Image | Port | Purpose |
|---|---|---|---|
| `web` | Built from Dockerfile | 8001 | FastAPI application |
| `postgres` | postgres:15 | 5433 | Relational database |
| `chromadb` | chromadb/chroma | 8002 | Vector database for AI search |

---

## Getting Started

### Requirements

- Docker & docker-compose
- Python 3.11+ (for local development without Docker)

### Environment Setup

```bash
cp .env.example .env
```

Fill in your values — `.env.example`:
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/web_db
CHROMA_HOST=localhost
CHROMA_PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
CRM_API_URL=http://localhost:8000
CRM_API_KEY=your-secret-api-key
```

> `CRM_API_KEY` must match `WEBSITE_API_KEY` in the CRM service `.env`.

### Run with Docker

```bash
make build   # Build images
make demo    # Start databases → run migrations → seed inventory → start web
```

App available at: `http://localhost:8001`

### Run Locally (without Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

docker-compose up -d postgres

alembic upgrade head
python scripts/seed.py

uvicorn app.main:app --port 8001 --reload
```

### Makefile Commands

```bash
make up                         # Start all services
make down                       # Stop containers and remove volumes
make build                      # Rebuild Docker images
make demo                       # Start DBs → migrate → seed → start web
make migrate                    # Run migrations (local dev)
make migration msg="add table"  # Generate new Alembic migration
make logs                       # Stream container logs
make freeze                     # Update requirements.txt
```

---

## Inventory

The inventory contains **60 vehicles**:

- **30 new vehicles** — 2026 Subaru lineup (Crosstrek, Forester, Outback, Solterra, Trailseeker, WRX, BRZ, Impreza, Ascent). Mileage under 10 miles.
- **30 used vehicles** — Mix of Japanese, American, European, and Korean makes from 2014 to 2022. Priced from $7,000 to $62,000.

Source data: `app/data/inventory.json`

---

## How Images Work

1. Model-specific image: `/static/img/models/{base_model}/{base_model}.jpg`
   - Example: `Forester Limited` → `/static/img/models/forester/forester.jpg`
2. Body-type fallback: `/static/img/types/{type}.jpg`
3. No image — renders a placeholder icon

---

## Planned Features

### AI Chat Assistant

The database schema and vector infrastructure are already in place for an AI-powered chat widget. Planned architecture:

```
Customer: "Looking for a Japanese SUV under $25k with AWD"
        ↓
ChromaDB — semantic vector search across vehicle inventory
        ↓
PostgreSQL — fetch full vehicle details by ID
        ↓
Ollama (llama3.2, local LLM) — generate natural language response
        ↓
Chat response with matching vehicles
```

- LangChain for orchestration
- ChromaDB for RAG (Retrieval-Augmented Generation)
- Conversation history stored in PostgreSQL (`chat_sessions`, `chat_messages`)

---

## Technical Notes

- **Async**: All routes use `async def` with `await`. Database layer uses `create_async_engine` + `asyncpg`. CRM calls use `httpx.AsyncClient`.
- **ORM**: SQLAlchemy 2.0 declarative models. Sessions injected via `Depends(get_db)`.
- **Migrations**: Alembic with autogenerate. Run `make migration msg="..."` to create, `make migrate` to apply.
- **Templates**: Jinja2 with `cache_size=0`. Template engine is a singleton in `app/core/templates.py`.
- **Filter pattern**: `_apply_range()` parses `under_X` / `over_X` string values into SQL WHERE clauses.
- **Error handling**: Unknown routes and invalid vehicle IDs redirect to homepage. CRM connection failures show an inline error on the form without crashing.
- **Seeding**: `scripts/seed.py` upserts vehicles, safe to re-run after schema changes.