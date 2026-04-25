# Galaxy Motors — Auto Dealer Web Application

A full-stack web application for a fictional auto dealership, built with Python and FastAPI. Customers can browse inventory, filter vehicles by condition, price, mileage, make, and year, and view detailed vehicle pages. The project is actively being extended with an AI-powered chat assistant backed by RAG (Retrieval-Augmented Generation).

> **Demo project for portfolio purposes only. Not a real dealership.**

---

## What It Does

- Browse a full inventory of 60 vehicles (30 new 2026 Subaru models, 30 used vehicles)
- Filter by condition, make, year, mileage, and price
- View individual vehicle pages with specs, features, and photos
- Navigate dealership pages: New Vehicles, Used Vehicles, About Us, Parts & Service
- Data is stored in PostgreSQL and served via a FastAPI backend with Jinja2 templates

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| Templating | Jinja2, Bootstrap 5.3 |
| Database | PostgreSQL 15, SQLAlchemy 2.0 |
| Migrations | Alembic |
| Vector DB | ChromaDB (for upcoming AI assistant) |
| AI / LLM | Ollama (llama3.2, local) — planned |
| AI Orchestration | LangChain — planned |
| Infrastructure | Docker, docker-compose |
| Configuration | Pydantic Settings, python-dotenv |

---

## Project Structure

```
auto-dealer-conversation-service/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── routes.py            # Router aggregator
│   │   ├── inventory.py         # Vehicle listing, search, detail routes
│   │   └── pages.py             # Static pages (About, Parts & Service)
│   ├── core/
│   │   ├── config.py            # Environment settings (Pydantic)
│   │   ├── database.py          # SQLAlchemy engine & session
│   │   └── templates.py         # Jinja2 template engine setup
│   ├── models/
│   │   ├── vehicle.py           # Vehicle ORM model
│   │   └── chat.py              # ChatSession & ChatMessage ORM models
│   ├── schemas/                 # Pydantic schemas (for AI chat API, upcoming)
│   ├── services/                # Business logic layer (upcoming)
│   ├── templates/
│   │   ├── base.html            # Base layout (topbar, navbar, footer)
│   │   ├── index.html           # Homepage with search & filter
│   │   ├── vehicle_list.html    # New / Used vehicle listing
│   │   ├── vehicle_detail.html  # Individual vehicle detail page
│   │   ├── about.html           # About Us page
│   │   └── parts_service.html   # Parts & Service page
│   ├── static/
│   │   ├── css/style.css        # Custom styles
│   │   └── img/
│   │       ├── types/           # Fallback images by body type (sedan, suv, truck)
│   │       └── models/          # Model-specific images (Subaru lineup)
│   └── data/
│       └── inventory.json       # Source inventory data (60 vehicles)
├── scripts/
│   └── seed.py                  # Seeds PostgreSQL + ChromaDB from inventory.json
├── alembic/                     # Database migrations
│   └── versions/
│       ├── 8b319c96dc1a_create_chat_tables.py
│       ├── d1be31a31ce3_add_vehicles_table.py
│       └── fe2a9887841c_add_condition_to_vehicles.py
├── tests/                       # Test suite (upcoming)
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
| GET | `/about` | About Us page |
| GET | `/parts-service` | Parts & Service page |
| GET | `/health` | Health check — returns `{"status": "ok"}` |

### Search Filter Parameters (`GET /`)

| Parameter | Type | Example | Description |
|---|---|---|---|
| `condition` | string | `new` / `used` | Vehicle condition |
| `year` | string | `2026` | Exact model year |
| `make` | string | `Subaru` | Manufacturer |
| `mileage_range` | string | `under_40000` | Mileage filter |
| `price_range` | string | `over_60000` | Price filter |

Filter values follow the pattern `under_X` or `over_X` (e.g. `under_30000`, `over_60000`).

---

## Infrastructure

Three services run via docker-compose:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `chatbot` | Built from Dockerfile | 8001 | FastAPI application |
| `postgres` | postgres:15 | 5433 | Relational database |
| `chromadb` | chromadb/chroma | 8002 | Vector database for AI search |

---

## Getting Started

### Requirements

- Docker & docker-compose
- Python 3.11+ (for local development without Docker)
- [Ollama](https://ollama.com) installed on host (for AI features, upcoming)

### Environment Setup

```bash
cp .env.example .env
```

`.env.example`:
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/chatbot_db
CHROMA_HOST=localhost
CHROMA_PORT=8002
OLLAMA_BASE_URL=http://localhost:11434
CRM_API_URL=http://localhost:8000
```

### Run with Docker

```bash
make build       # Build images
make demo        # Start databases → run migrations → seed inventory → start web
```

App available at: `http://localhost:8001`

> **Note:** `docker-compose.yml` overrides `DATABASE_URL` and `CHROMA_HOST` for the container environment, so the app connects to internal Docker service names (`postgres`, `chromadb`) rather than `localhost`.

### Run Locally (without Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

docker-compose up -d postgres   # Start only the database

alembic upgrade head            # Run migrations
python scripts/seed.py          # Seed inventory

uvicorn app.main:app --port 8001 --reload
```

### Makefile Commands

```bash
make up                          # Start all services in background
make down                        # Stop containers and remove volumes
make build                       # Rebuild Docker images
make demo                        # Start DBs → migrate → seed → start web
make migrate                     # Run migrations only (local dev)
make migration msg="add table"   # Generate new Alembic migration
make logs                        # Stream container logs
make freeze                      # Update requirements.txt
```

---

## Inventory

The inventory contains **60 vehicles**:

- **30 new vehicles** — 2026 Subaru lineup (Crosstrek, Forester, Outback, Solterra, Trailseeker, WRX, BRZ, Impreza, Ascent) across multiple trim levels. Mileage under 10 miles. Current market pricing.
- **30 used vehicles** — Mix of Japanese, American, European, and Korean makes from 2014–2022. Priced from $7,000 to $62,000.

Source data: `app/data/inventory.json`

---

## How Images Work

Vehicle detail pages use the following fallback logic:

1. Look for a model-specific image in `/static/img/models/{base_model}/`
   - Example: `Forester Limited` → `/static/img/models/forester/forester.jpg`
2. Fall back to a body-type image in `/static/img/types/{type}.jpg`
   - Example: type `sedan` → `/static/img/types/sedan.jpg`
3. If no image found — renders a placeholder icon

---

## Planned Features

### AI Chat Assistant
The database schema and vector infrastructure are already in place for an AI-powered chat widget (bottom-right corner of the site). Planned architecture:

```
Customer types: "Looking for a Japanese SUV under $25k with AWD"
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
- REST API endpoints for chat with Pydantic request/response schemas

---

## Technical Notes

- **ORM**: SQLAlchemy 2.0 with declarative models. Sessions injected via FastAPI `Depends(get_db)`.
- **Migrations**: Alembic with autogenerate. Run `make migration msg="..."` to create, `make migrate` to apply.
- **Templates**: Jinja2 with `cache_size=0` (dev mode). Template engine is a singleton in `app/core/templates.py`.
- **Image serving**: FastAPI `StaticFiles` mounted at `/static`. Image resolution logic lives in `inventory.py:_get_vehicle_image()`.
- **Filter pattern**: Price and mileage use a `_apply_range()` helper that parses `under_X` / `over_X` string values into SQL filters — avoids the common type-coercion bugs when mixing string query params with numeric DB filters.
- **Seeding**: `scripts/seed.py` upserts vehicles (not insert-only), so it's safe to re-run after schema changes.