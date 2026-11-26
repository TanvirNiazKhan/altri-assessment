"""Rules report on a freshly seeded database: golden file at the default APP_NOW, plus
spot checks at other dates (the report must compute everything from the data)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from src.config.database import build_engine, build_sessionmaker
from src.config.dependency import build_rules_report_service
from src.config.settings import DEFAULT_APP_NOW, Settings
from src.infra.database.repositories import SqlCompanyRepository
from src.infra.realtime.publisher import NullEventPublisher

pytestmark = pytest.mark.db
GOLDEN = Path(__file__).resolve().parents[3] / "rules_report.json"


async def report_at(settings: Settings, now: datetime) -> dict[str, Any]:
    engine = build_engine(settings)
    try:
        async with build_sessionmaker(engine)() as session:
            (company,) = await SqlCompanyRepository(session).list_all()
            service = build_rules_report_service(session, NullEventPublisher())
            report: dict[str, Any] = await service.build(company, now)
            # Round-trip through JSON exactly as the CLI prints it.
            return json.loads(json.dumps(report))  # type: ignore[no-any-return]
    finally:
        await engine.dispose()


@pytest.mark.skipif(not GOLDEN.exists(), reason="rules_report.json not mounted")
async def test_matches_committed_rules_report(settings: Settings) -> None:
    assert await report_at(settings, DEFAULT_APP_NOW) == json.loads(GOLDEN.read_text())


async def test_report_one_week_later(settings: Settings) -> None:
    lead = (await report_at(settings, datetime(2026, 11, 18, 15, tzinfo=UTC)))["teams"]["team_lead"]
    weeks = list(lead["measurable_status"]["m1"])
    assert (weeks[0], weeks[-1]) == ("2026-08-24", "2026-11-16")
    assert lead["measurable_status"]["m5"]["2026-11-09"] == "on_track"
    assert lead["measurable_status"]["m1"]["2026-11-09"] == "off_track"  # now closed, no score
    assert lead["measurable_status"]["m1"]["2026-11-16"] == "pending"
    assert "t30" in lead["overdue_todos"]  # due Nov 11, not done
    assert lead["todo_completion"]["2026-11-09"]["due"] == 3
    assert lead["rocks"]["r1"]["status"] == "off_track"  # ms2 (due Nov 11) now past due


async def test_report_before_second_meeting_ended(settings: Settings) -> None:
    """Nov 4 15:30Z: mt2 (ended 16:20Z) has not ended; i6 (solved 15:40Z) is still open."""
    lead = (await report_at(settings, datetime(2026, 11, 4, 15, 30, tzinfo=UTC)))["teams"][
        "team_lead"
    ]
    assert list(lead["meetings"]) == ["mt1"]
    assert "i6" in lead["issue_order"]
    assert "i5" not in lead["issue_order"]  # created Nov 9
