from decimal import Decimal

from src.domain.modules.meeting.entity import AGENDA, MeetingSection, average_rating
from src.domain.shared.numbers import round_half_up


def test_average_rating_half_up() -> None:
    assert average_rating([8, 9, 7]) == Decimal("8.0")
    assert average_rating([8, 9, 8, 8]) == Decimal("8.3")  # 8.25; banker's would give 8.2
    assert average_rating([]) is None


def test_round_half_up() -> None:
    assert round_half_up(Decimal("12.5")) == 13
    assert round_half_up(Decimal("8.25"), 1) == Decimal("8.3")


def test_agenda_order_and_durations() -> None:
    assert [(s, d // 60) for s, d in AGENDA] == [
        (MeetingSection.SCORECARD, 5),
        (MeetingSection.IDS, 60),
        (MeetingSection.CONCLUDE, 10),
    ]
