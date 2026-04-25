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
	docker-compose up -d postgres chromadb
	sleep 5
	docker-compose run --rm web alembic upgrade head
	docker-compose run --rm web python scripts/seed.py
	docker-compose up -d web

logs:
	docker-compose logs -f

freeze:
	pip freeze > requirements.txt