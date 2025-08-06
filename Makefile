ifneq (,$(wildcard ./.env))
include .env
export
ENV_FILE_PARAM = --env-file .env
else
  $(error .env file not found or empty)
endif

# Configuración de entorno
ENVIRONMENT ?= development
COMPOSE_FILE = docker-compose.yml

# Seleccionar archivo de compose según el entorno
ifeq ($(ENVIRONMENT),production)
	COMPOSE_FILE = docker-compose.prod.yml
else ifeq ($(ENVIRONMENT),staging)
	COMPOSE_FILE = docker-compose.staging.yml
endif

# Comandos principales
build:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) up --build -d --remove-orphans

up:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down

down-v:
	docker compose -f $(COMPOSE_FILE) down -v

show-logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Configuración de entornos
set-dev:
	@echo "🔧 Configurando entorno de desarrollo..."
	@./scripts/set-environment.sh development

set-staging:
	@echo "🔧 Configurando entorno de staging..."
	@./scripts/set-environment.sh staging

set-prod:
	@echo "🔧 Configurando entorno de producción..."
	@./scripts/set-environment.sh production

# Comandos de desarrollo

shell:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py shell

migrate:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py migrate

makemigrations:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py makemigrations

superuser:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py createsuperuser

collectstatic:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py collectstatic --no-input --clear

# Comandos específicos de entorno
dev-server:
	DJANGO_ENVIRONMENT=development python manage.py runserver 0.0.0.0:8000

dev-migrate:
	DJANGO_ENVIRONMENT=development python manage.py migrate

dev-makemigrations:
	DJANGO_ENVIRONMENT=development python manage.py makemigrations

staging-deploy:
	@echo "🚀 Desplegando en staging..."
	ENVIRONMENT=staging make build
	DJANGO_ENVIRONMENT=staging docker compose -f docker-compose.staging.yml exec api python3 manage.py migrate
	DJANGO_ENVIRONMENT=staging docker compose -f docker-compose.staging.yml exec api python3 manage.py collectstatic --noinput

prod-deploy:
	@echo "🚀 Desplegando en producción..."
	ENVIRONMENT=production make build
	DJANGO_ENVIRONMENT=production docker compose -f docker-compose.prod.yml exec api python3 manage.py migrate
	DJANGO_ENVIRONMENT=production docker compose -f docker-compose.prod.yml exec api python3 manage.py collectstatic --noinput

# Utilidades
check-config:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) python manage.py check

test:
	DJANGO_ENVIRONMENT=development python manage.py test

coverage:
	DJANGO_ENVIRONMENT=development coverage run --source='.' manage.py test
	coverage report -m
	coverage html

# Comandos de mantenimiento

sync-stripe-customers:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py sync_stripe_customers

wait-for-redis:
	DJANGO_ENVIRONMENT=$(ENVIRONMENT) docker compose -f $(COMPOSE_FILE) exec api python3 manage.py wait_for_redis --timeout 5 --interval 0.5

volume:
	docker volume inspect shop-eline_postgres_data

eline-db:
	docker compose -f $(COMPOSE_FILE) exec postgres-db psql --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB)

clean:
	docker system prune -f
	docker volume prune -f

backup-db:
	@echo "📦 Creando backup de base de datos..."
	docker compose -f $(COMPOSE_FILE) exec postgres-db pg_dump --username=$(POSTGRES_USER) --dbname=$(POSTGRES_DB) > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Comandos de ayuda
help:
	@echo "🚀 Comandos disponibles:"
	@echo ""
	@echo "📋 Configuración de entornos:"
	@echo "  make set-dev      - Configurar entorno de desarrollo"
	@echo "  make set-staging  - Configurar entorno de staging"
	@echo "  make set-prod     - Configurar entorno de producción"
	@echo ""
	@echo "🏗️  Construcción y ejecución:"
	@echo "  make build        - Construir contenedores"
	@echo "  make up           - Levantar servicios"
	@echo "  make down         - Parar servicios"
	@echo "  make down-v       - Parar servicios y eliminar volúmenes"
	@echo ""
	@echo "🔧 Desarrollo:"
	@echo "  make dev-server   - Ejecutar servidor de desarrollo"
	@echo "  make shell        - Abrir shell de Django"
	@echo "  make migrate      - Ejecutar migraciones"
	@echo "  make makemigrations - Crear migraciones"
	@echo "  make test         - Ejecutar tests"
	@echo ""
	@echo "🚀 Despliegue:"
	@echo "  make staging-deploy - Desplegar en staging"
	@echo "  make prod-deploy    - Desplegar en producción"
	@echo ""
	@echo "📊 Utilidades:"
	@echo "  make show-logs    - Ver logs"
	@echo "  make check-config - Verificar configuración"
	@echo "  make backup-db    - Crear backup de BD"
	@echo "  make clean        - Limpiar Docker"

.PHONY: build up down down-v show-logs shell migrate makemigrations superuser collectstatic \
        set-dev set-staging set-prod dev-server dev-migrate dev-makemigrations \
        staging-deploy prod-deploy check-config test coverage clean backup-db help

pip-freeze:
	docker compose exec api pip freeze

pip-review:
	docker compose exec api pip-review --local --interactive

pip-outdated:
	docker compose exec api pip list --outdated --format=columns

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
