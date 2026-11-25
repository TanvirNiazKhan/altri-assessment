COMPOSE := docker compose
API := $(COMPOSE) run --rm -T -e RUN_MIGRATIONS=0 -e RUN_SEED=0 api
TEST_DB := postgresql+asyncpg://l10:l10@db:5432/l10

.PHONY: up down logs build migrate revision seed reset test lint typecheck check

up:            ## Start the stack (migrates and seeds on boot)
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

build:
	$(COMPOSE) build api

migrate:       ## Apply migrations
	$(API) alembic upgrade head

revision:      ## make revision m="add foo"
	$(API) alembic revision --autogenerate -m "$(m)"

seed:          ## Idempotent seed
	$(API) python -m src.cli seed

reset:         ## Truncate and reseed
	$(API) python -m src.cli reset

test: build    ## All tests, unattended; each DB test gets its own seeded database
	$(COMPOSE) up -d --wait db
	$(COMPOSE) run --rm -T -e RUN_MIGRATIONS=0 -e RUN_SEED=0 \
	  -e TEST_DATABASE_URL=$(TEST_DB) api pytest -p no:cacheprovider

lint:
	$(API) sh -c "ruff check . && ruff format --check ."

typecheck:
	$(API) mypy src tests

check: lint typecheck test
