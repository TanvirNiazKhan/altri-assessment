#!/bin/sh
# Container entrypoint: migrate, seed (idempotent), then run the given command.
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    alembic upgrade head
fi

if [ "${RUN_SEED:-1}" = "1" ]; then
    python -m src.cli seed
fi

exec "$@"
