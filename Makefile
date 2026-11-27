COMPOSE := docker compose
API := $(COMPOSE) run --rm -T -e RUN_MIGRATIONS=0 -e RUN_SEED=0 api
TEST_DB := postgresql+asyncpg://l10:l10@db:5432/l10

.PHONY: up down logs build migrate revision seed reset test test-api e2e rules-report lint typecheck check

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

test: test-api ## All tests (unattended)

test-api: build ## Rule, API, real-time and rules-report tests; each DB test gets its own seeded DB
	$(COMPOSE) up -d --wait db
	$(COMPOSE) run --rm -T -e RUN_MIGRATIONS=0 -e RUN_SEED=0 \
	  -e TEST_DATABASE_URL=$(TEST_DB) \
	  -v "$(CURDIR)/rules_report.json:/rules_report.json:ro" \
	  api pytest -p no:cacheprovider

rules-report: build ## Regenerate rules_report.json (fresh seeded DB, APP_NOW; override APP_NOW=...)
	$(COMPOSE) up -d --wait db
	$(COMPOSE) run --rm -T -e RUN_MIGRATIONS=0 -e RUN_SEED=0 -e LOG_LEVEL=WARNING \
	  -e APP_NOW=$${APP_NOW:-2026-11-11T15:00:00Z} \
	  api python -m src.cli rules-report > rules_report.json
	@echo "wrote rules_report.json"

e2e:           ## Playwright, two browsers in one meeting, against the running stack (make up first)
	cd frontend && npm ci && npx playwright install chromium && npx playwright test

lint:
	$(API) sh -c "ruff check . && ruff format --check ."

typecheck:
	$(API) mypy src tests

check: lint typecheck test
