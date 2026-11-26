"""Wire format of team events on the Postgres NOTIFY channel."""

import json

from src.domain.shared.events import TeamEvent, Topic

CHANNEL = "team_events"


def encode(event: TeamEvent) -> str:
    return json.dumps(
        {
            "team_id": event.team_id,
            "topics": sorted(t.value for t in event.topics),
            "meeting_id": event.meeting_id,
        },
        separators=(",", ":"),
    )


def decode(payload: str) -> TeamEvent:
    data = json.loads(payload)
    return TeamEvent(
        team_id=str(data["team_id"]),
        topics=frozenset(Topic(t) for t in data["topics"]),
        meeting_id=data.get("meeting_id"),
    )
