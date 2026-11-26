"""Operational commands.

    python -m src.cli seed                     load seed.json if not loaded (idempotent)
    python -m src.cli reset                    truncate every table and reseed
    python -m src.cli rules-report             rules report JSON for a *freshly seeded* DB
    python -m src.cli rules-report --current-db  ... for the configured DB as it is now

"Now" is APP_NOW (frozen; the report never reads the system clock).
"""

import argparse
import asyncio
import json
import logging
import sys
import uuid
from typing import Any

from src.config.database import build_engine, build_sessionmaker
from src.config.dependency import build_rules_report_service
from src.config.logging import configure_logging
from src.config.settings import Settings, get_settings
from src.infra.database.provisioning import create_database, drop_database, migrate_and_seed
from src.infra.database.repositories import SqlCompanyRepository
from src.infra.database.seed.loader import load_seed, read_seed, truncate_all
from src.infra.realtime.publisher import NullEventPublisher

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


async def _report_for(settings: Settings) -> dict[str, Any]:
    engine = build_engine(settings)
    try:
        async with build_sessionmaker(engine)() as session:
            report: dict[str, Any] = {"now": None, "teams": {}}
            service = build_rules_report_service(session, NullEventPublisher())
            for company in await SqlCompanyRepository(session).list_all():
                part = await service.build(company, settings.app_now)
                report["now"] = part["now"]
                report["teams"].update(part["teams"])
            return report
    finally:
        await engine.dispose()


async def _rules_report(*, current_db: bool) -> dict[str, Any]:
    settings = get_settings()
    if current_db:
        return await _report_for(settings)
    name = f"l10_report_{uuid.uuid4().hex[:12]}"
    url = await create_database(settings.database_url, name)
    try:
        await migrate_and_seed(url, settings.seed_path)
        return await _report_for(settings.model_copy(update={"database_url": url}))
    finally:
        await drop_database(settings.database_url, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="src.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Load seed.json if not already loaded (idempotent)")
    sub.add_parser("reset", help="Truncate every table and reseed")
    report = sub.add_parser("rules-report", help="Print the rules report JSON (brief 2.6)")
    report.add_argument(
        "--current-db",
        action="store_true",
        help="Use the configured database as-is instead of a fresh seeded copy",
    )
    args = parser.parse_args(argv)

    configure_logging(get_settings().log_level)
    if args.command == "rules-report":
        result = asyncio.run(_rules_report(current_db=args.current_db))
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        asyncio.run(_seed(reset=args.command == "reset"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
