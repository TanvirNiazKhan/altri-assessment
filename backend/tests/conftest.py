"""Fixture and clock strategy.

* Clock: every app under test gets a FrozenClock at APP_NOW (2026-11-11T15:00:00Z), so
  "today", the current week and overdue flags are fixed. Timer tests call `clock.advance()`.
* Database: once per session, a template database is created, migrated and seeded.
  Every `@pytest.mark.db` test then gets its own copy (`CREATE DATABASE ... TEMPLATE`),
  so tests can write freely, run real concurrent transactions, and never see each
  other's data. Without TEST_DATABASE_URL, `db` tests are skipped.
"""

import asyncio
import os
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.config.settings import DEFAULT_APP_NOW, Settings
from src.infra.database.provisioning import create_database, drop_database, migrate_and_seed
from src.infra.services.clock import FrozenClock
from src.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
TEMPLATE_DB = "l10_test_template"
UNUSED_URL = "postgresql+asyncpg://unused:unused@localhost:1/unused"

LoginAs = Callable[[str], Awaitable[AsyncClient]]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if TEST_DATABASE_URL:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL not set")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def template_db() -> Iterator[str]:
    assert TEST_DATABASE_URL
    settings = Settings()
    asyncio.run(drop_database(TEST_DATABASE_URL, TEMPLATE_DB))
    url = asyncio.run(create_database(TEST_DATABASE_URL, TEMPLATE_DB))
    asyncio.run(migrate_and_seed(url, settings.seed_path))
    yield TEMPLATE_DB
    asyncio.run(drop_database(TEST_DATABASE_URL, TEMPLATE_DB))


@pytest.fixture
def database_url(request: pytest.FixtureRequest) -> Iterator[str]:
    """A private, freshly seeded database for `db` tests; a dummy URL otherwise."""
    if request.node.get_closest_marker("db") is None:
        yield UNUSED_URL
        return
    assert TEST_DATABASE_URL
    template = request.getfixturevalue("template_db")
    name = f"l10_test_{uuid.uuid4().hex[:12]}"
    url = asyncio.run(create_database(TEST_DATABASE_URL, name, template=template))
    yield url
    asyncio.run(drop_database(TEST_DATABASE_URL, name))


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(DEFAULT_APP_NOW)


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=database_url,
        app_clock_mode="frozen",
        session_secret="test-secret",
        realtime_enabled=database_url != UNUSED_URL,
        log_level="WARNING",
    )


@pytest.fixture
async def app(settings: Settings, clock: FrozenClock) -> AsyncIterator[FastAPI]:
    application = create_app(settings, clock)
    async with LifespanManager(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def login_as(app: FastAPI) -> AsyncIterator[LoginAs]:
    """`await login_as("u2")` -> a client with u2's session cookie (one cookie jar each)."""
    clients: list[AsyncClient] = []

    async def make(user_id: str) -> AsyncClient:
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        clients.append(c)
        r = await c.post("/api/auth/login", json={"user_id": user_id})
        assert r.status_code == 200, r.text
        return c

    yield make
    for c in clients:
        await c.aclose()
