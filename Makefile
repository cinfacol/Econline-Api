ifneq (,$(wildcard ./.env))
include .env
export
ENV_FILE_PARAM = --env-file .env
else
  $(error .env file not found or empty)
endif

build:
	docker compose up --build -d --remove-orphans

up:
	docker compose up -d

down:
	docker compose down

down-v:
	docker compose down -v

show-logs:
	docker compose logs -f


shell:
	docker compose exec api python3 manage.py shell

migrate:
	docker compose exec api python3 manage.py migrate

makemigrations:
	docker compose exec api python3 manage.py makemigrations

superuser:
	docker compose exec api python3 manage.py createsuperuser

sync-stripe-customers:
	docker compose exec api python3 manage.py sync_stripe_customers

collectstatic:
	docker compose exec api python3 manage.py collectstatic --no-input --clear

volume:
	docker volume inspect shop-eline_postgres_data

eline-db:
	docker compose exec postgres-db psql --username=postgres --dbname=shop-eline

pip-freeze:
	docker compose exec api pip freeze

pip-review:
	docker compose exec api pip-review --local --interactive

test:
	docker compose exec api pytest -p no:warnings --cov=.

test-payments:
	docker compose exec api python3 manage.py test payments

test-html:
	docker compose exec api pytest -p no:warnings --cov=. --cov-report html

flake8:
	docker compose exec api flake8 .

black-check:
	docker compose exec api black --check --exclude=migrations .

black-diff:
	docker compose exec api black --diff --exclude=migrations .

black:
	docker compose exec api black --exclude=migrations .

isort-check:
	docker compose exec api isort . --check-only --skip env --skip migrations

isort-diff:
	docker compose exec api isort . --diff --skip env --skip migrations

isort:
	docker compose exec api isort . --skip env --skip migrations
