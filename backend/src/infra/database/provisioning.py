"""Create, migrate, seed and drop databases (rules report on a fresh DB, test isolation)."""

import asyncio
import re
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infra.database.seed.loader import load_seed, read_seed

BACKEND_ROOT = Path(__file__).resolve().parents[3]
_SAFE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def with_database(url: str, name: str) -> str:
    return make_url(url).set(database=name).render_as_string(hide_password=False)


def _check(name: str) -> str:
    if not _SAFE_NAME.match(name):
        raise ValueError(f"unsafe database name: {name!r}")
    return name


async def _admin(url: str, sql: str) -> None:
    engine = create_async_engine(with_database(url, "postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(text(sql))
    finally:
        await engine.dispose()


async def create_database(url: str, name: str, *, template: str | None = None) -> str:
    """Create `name` on the server of `url` and return its URL."""
    sql = f'CREATE DATABASE "{_check(name)}"'
    if template:
        sql += f' TEMPLATE "{_check(template)}"'
    await _admin(url, sql)
    return with_database(url, name)


async def drop_database(url: str, name: str) -> None:
    await _admin(url, f'DROP DATABASE IF EXISTS "{_check(name)}" WITH (FORCE)')


def migrate(url: str) -> None:
    """alembic upgrade head. Synchronous (env.py runs its own event loop): call from a thread."""
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")


async def migrate_and_seed(url: str, seed_path: Path) -> None:
    await asyncio.to_thread(migrate, url)
    engine = create_async_engine(url)
    try:
        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        async with sessionmaker() as session, session.begin():
            await load_seed(session, read_seed(seed_path))
    finally:
        await engine.dispose()
