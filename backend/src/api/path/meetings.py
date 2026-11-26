from fastapi import APIRouter, status

from src.api.schemas.common import PROBLEM_RESPONSES, IdPath
from src.api.schemas.meeting import (
    AdvanceRequest,
    MeetingListItemResponse,
    MeetingStateResponse,
    MeetingSummaryResponse,
    RatingRequest,
)
from src.config.dependency import CalendarDep, MeetingServiceDep, ReadTeam, WriteTeam

router = APIRouter(
    prefix="/teams/{team_id}/meetings", tags=["meetings"], responses=PROBLEM_RESPONSES
)


@router.get("/active", summary="The team's active meeting, or null")
async def get_active(
    access: ReadTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingStateResponse:
    return MeetingStateResponse.build(await meetings.active_state(access.team.id), cal.now)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Start a meeting; the caller becomes facilitator (409 if one is active)",
)
async def start_meeting(
    access: WriteTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingStateResponse:
    return MeetingStateResponse.build(await meetings.start(access, cal), cal.now)


@router.get("", summary="Ended meetings, most recent first")
async def list_meetings(
    access: ReadTeam, meetings: MeetingServiceDep
) -> list[MeetingListItemResponse]:
    return [
        MeetingListItemResponse.from_domain(m) for m in await meetings.list_ended(access.team.id)
    ]


@router.get("/{meeting_id}", summary="A meeting's state (active or ended)")
async def get_meeting(
    meeting_id: IdPath, access: ReadTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingStateResponse:
    return MeetingStateResponse.build(await meetings.state(access.team.id, meeting_id), cal.now)


@router.post("/{meeting_id}/join", summary="Record attendance (idempotent; Observers allowed)")
async def join_meeting(
    meeting_id: IdPath, access: ReadTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingStateResponse:
    return MeetingStateResponse.build(await meetings.join(access, meeting_id, cal), cal.now)


@router.post("/{meeting_id}/advance", summary="Facilitator moves to the next section")
async def advance_meeting(
    meeting_id: IdPath,
    body: AdvanceRequest,
    access: WriteTeam,
    cal: CalendarDep,
    meetings: MeetingServiceDep,
) -> MeetingStateResponse:
    state = await meetings.advance(access, meeting_id, body.expected_section, cal)
    return MeetingStateResponse.build(state, cal.now)


@router.post("/{meeting_id}/end", summary="Facilitator ends the meeting; summary is frozen")
async def end_meeting(
    meeting_id: IdPath, access: WriteTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingStateResponse:
    return MeetingStateResponse.build(await meetings.end(access, meeting_id, cal), cal.now)


@router.put("/{meeting_id}/rating", summary="Rate 1-10 during Conclude (changeable until the end)")
async def rate_meeting(
    meeting_id: IdPath,
    body: RatingRequest,
    access: WriteTeam,
    cal: CalendarDep,
    meetings: MeetingServiceDep,
) -> MeetingStateResponse:
    state = await meetings.rate(access, meeting_id, body.rating, cal)
    return MeetingStateResponse.build(state, cal.now)


@router.get("/{meeting_id}/summary", summary="Summary of an ended meeting (frozen snapshot)")
async def get_summary(
    meeting_id: IdPath, access: ReadTeam, cal: CalendarDep, meetings: MeetingServiceDep
) -> MeetingSummaryResponse:
    summary = await meetings.summary(access.team.id, meeting_id, cal.tz)
    return MeetingSummaryResponse.from_domain(summary)
