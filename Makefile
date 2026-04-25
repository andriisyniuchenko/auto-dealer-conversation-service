.PHONY: up down reset build db migrate migration logs freeze

up:
	docker-compose up -d

down:
	docker-compose down

reset:
	docker-compose down -v

build:
	docker-compose up --build -d

db:
	docker-compose up -d postgres

demo:
	docker-compose run --rm chatbot python scripts/seed.py

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

logs:
	docker-compose logs -f

freeze:
	pip freeze > requirements.txt