# Auto Dealer Conversation Service

AI-powered chatbot service for auto dealerships. Customers describe what they're looking for in natural language, and the bot finds matching vehicles from the inventory using semantic search.

## Overview

- Customers interact via a chat UI and describe their needs (e.g. *"Japanese car under $15k, automatic, under 80k miles"*)
- The bot searches a vector database of vehicles using RAG (Retrieval-Augmented Generation)
- Conversation context is preserved — follow-up questions work naturally
- Dealership staff view full chat histories per customer in the CRM

## Architecture

```
[Client Browser]
      | HTTP
[FastAPI :8001]
      |
[LangChain] --> [ChromaDB - vehicle inventory vectors]
      |
[Ollama - local LLM (llama3.2)]
      |
[PostgreSQL - chat history]
      ^
[CRM API :8000] <-- staff views chat history
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| AI Orchestration | LangChain, langchain-ollama |
| Vector DB | ChromaDB |
| LLM | Ollama (local) |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Templating | Jinja2 |
| HTTP Client | httpx |
| Infrastructure | Docker, docker-compose |


## Status

> Work in progress. Initial scaffolding in progress.

## Requirements

- Docker & docker-compose
- [Ollama](https://ollama.com) installed on host machine

## Getting Started

_Setup instructions will be added as the service is built out._