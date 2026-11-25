"""Operational commands: `python -m src.cli {seed,reset}`."""

import argparse
import asyncio
import logging
import sys

from src.config.database import build_engine, build_sessionmaker
from src.config.logging import configure_logging
from src.config.settings import get_settings
from src.infra.database.seed.loader import load_seed, read_seed, truncate_all

log = logging.getLogger("src.cli")


async def _seed(*, reset: bool) -> None:
    settings = get_settings()
    engine = build_engine(settings)
    try:
        async with build_sessionmaker(engine)() as session, session.begin():
            if reset:
                await truncate_all(session)
            inserted = await load_seed(session, read_seed(settings.seed_path))
        log.info("seed: %s", "inserted" if inserted else "already present, skipped")
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="src.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Load seed.json if not already loaded (idempotent)")
    sub.add_parser("reset", help="Truncate every table and reseed")
    args = parser.parse_args(argv)

    configure_logging(get_settings().log_level)
    asyncio.run(_seed(reset=args.command == "reset"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
