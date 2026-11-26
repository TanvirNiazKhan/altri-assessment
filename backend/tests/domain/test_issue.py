from datetime import UTC, datetime

from src.domain.modules.issue.entity import Issue, order_issues


def issue(id_: str, priority: int | None, created: datetime) -> Issue:
    return Issue(
        id=id_, team_id="tm", owner_id="u", title="x", created_at=created, priority=priority
    )


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def test_order_priority_desc_then_oldest_then_no_priority_last() -> None:
    issues = [
        issue("i4", None, utc(2026, 10, 1)),
        issue("i1", 5, utc(2026, 10, 20)),
        issue("i3", 3, utc(2026, 10, 1)),
        issue("i2", 5, utc(2026, 10, 14)),
        issue("i5", 4, utc(2026, 11, 9)),
    ]
    assert [i.id for i in order_issues(issues)] == ["i2", "i1", "i5", "i3", "i4"]


def test_id_breaks_exact_ties() -> None:
    t = utc(2026, 10, 1)
    assert [i.id for i in order_issues([issue("i9", 3, t), issue("i10", 3, t)])] == ["i10", "i9"]


def test_open_as_of_now() -> None:
    now = utc(2026, 11, 11, 15)
    solved_later = Issue("i", "tm", "u", "x", utc(2026, 11, 1), solved_at=utc(2026, 11, 12))
    assert solved_later.is_open_as_of(now)
    assert not issue("i", None, utc(2026, 11, 12)).is_open_as_of(now)  # created after now
