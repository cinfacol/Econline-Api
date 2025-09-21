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
	docker compose exec api uv pip list

pip-review:
	docker compose exec api uv pip list --outdated

pip-outdated:
	docker compose exec api uv pip list --outdated

# Comandos modernos con uv y pyproject.toml
uv-add:
	uv add $(PACKAGE)

uv-add-dev:
	uv add --dev $(PACKAGE)

uv-add-test:
	uv add --optional test $(PACKAGE)

uv-add-prod:
	uv add --optional prod $(PACKAGE)

uv-remove:
	uv remove $(PACKAGE)

uv-sync:
	uv sync

uv-sync-dev:
	uv sync --dev

uv-lock:
	uv lock

uv-lock-upgrade:
	uv lock --upgrade

uv-run:
	uv run $(COMMAND)

# Comandos para desarrollo con uv
uv-shell:
	uv run python manage.py shell

uv-migrate:
	uv run python manage.py migrate

uv-makemigrations:
	uv run python manage.py makemigrations

uv-test:
	uv run pytest -p no:warnings --cov=.

uv-black:
	uv run black --exclude=migrations .

uv-flake8:
	uv run flake8 .

uv-isort:
	uv run isort . --skip env --skip migrations

# Comandos Docker con uv (para uso con contenedores)
docker-uv-add:
	docker compose exec api uv add $(PACKAGE)

docker-uv-remove:
	docker compose exec api uv remove $(PACKAGE)

docker-uv-sync:
	docker compose exec api uv sync

test:
	docker compose exec api pytest -p no:warnings --cov=.

test-payments:
	docker compose exec api python3 manage.py test payments

test-html:
	docker compose exec api pytest -p no:warnings --cov=. --cov-report html

# ===== RUFF COMMANDS (Modern replacement for black, flake8, isort) =====
lint:
	docker compose exec api ruff check .

lint-fix:
	docker compose exec api ruff check . --fix

format:
	docker compose exec api ruff format .

format-check:
	docker compose exec api ruff format . --check

format-diff:
	docker compose exec api ruff format . --diff

# Combined command: fix linting and format code
fix:
	docker compose exec api ruff check . --fix
	docker compose exec api ruff format .