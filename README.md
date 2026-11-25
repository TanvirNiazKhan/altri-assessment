# altri-assessment: Level 10 Meeting App

A team operating system in the EOS style. Teams track weekly **Measurables** (Scorecard), quarterly **Rocks**, **To-Dos** and **Issues**, and run a live **Level 10 Meeting**.

> Work in progress. This commit sets up the project structure and foundations; features land in follow-up commits.

## Setup

Requires Docker.

```bash
docker compose up --build    # Postgres + API; migrations and the seed run on boot (rerun-safe)
open http://localhost:8000/api/docs
```

| Command | What it does |
|---|---|
| `make test` | Run all tests (unattended, in the API container) |
| `make check` | Lint (ruff) + types (mypy --strict) + tests |
| `make reset` | Truncate and reseed |
| `make revision m="..."` | Autogenerate a migration |

## Backend structure

Clean architecture; dependencies point inward: `api → config/dependency → domain ← infra`.

```
backend/src/
├── main.py           app factory: lifespan, middleware, routes
├── cli.py            seed | reset
├── api/              path/ (routers) · schemas/ · middlewares/ (problem+json errors, request id)
├── domain/           modules/<x>/{entity, repository (ABC), service, exceptions} · shared/
├── infra/            database/ (models, repositories, migrations support, seed) · adapters/ · services/ · cache/
└── config/           settings · database · dependency (DI) · logging
```

- **`domain`** is framework-free; a test enforces the layer boundaries.
- **Services** depend on repository interfaces; `infra` implements them.
- **Invariants** live in Postgres too: CHECKs, team-scoped composite FKs, partial unique indexes and triggers.
- **Time** comes from `APP_NOW` (default `2026-11-11T15:00:00Z`) through an injected clock. Nothing reads the system clock.
