.PHONY: up down reset build db migrate migration logs
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

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

logs:
	docker-compose logs -f