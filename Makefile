.PHONY: up down build migrate migration demo logs freeze

up:
	docker-compose up -d

down:
	docker-compose down -v

build:
	docker-compose up --build -d

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

demo:
	@echo "⚠️  Make sure Ollama is running locally with nomic-embed-text pulled:"
	@echo "    ollama pull nomic-embed-text"
	@echo ""
	docker-compose up -d postgres opensearch
	sleep 10
	docker-compose run --rm --build web alembic upgrade head
	docker-compose run --rm web python scripts/seed.py
	docker-compose up --build -d web

logs:
	docker-compose logs -f

freeze:
	pip freeze > requirements.txt