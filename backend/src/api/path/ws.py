from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.api.realtime.dispatcher import SocketSubscriber, TeamEventDispatcher
from src.config.dependency import build_team_service, build_user_service
from src.config.settings import Settings
from src.domain.shared.exceptions import DomainError
from src.infra.adapters.session_signer import SessionSigner
from src.infra.realtime.hub import ConnectionHub

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/teams/{team_id}")
async def team_socket(websocket: WebSocket, team_id: str) -> None:
    """Server -> client stream for one team. Authenticated with the session cookie and the
    same read check as REST. On (re)connect the current meeting state is sent immediately,
    so late joins, refreshes and reconnects recover without extra calls."""
    state = websocket.app.state
    settings: Settings = state.settings
    signer: SessionSigner = state.session_signer
    hub: ConnectionHub = state.hub
    dispatcher: TeamEventDispatcher = state.dispatcher

    async with state.sessionmaker() as session:
        try:
            token = websocket.cookies.get(settings.session_cookie_name)
            user = await build_user_service(session).resolve_session_user(signer.unsign(token))
            await build_team_service(session).authorize(user, team_id, write=False)
        except DomainError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await websocket.accept()
    subscriber = SocketSubscriber(websocket)
    hub.add(team_id, subscriber)  # before the snapshot, so no event can fall in between
    try:
        await subscriber.send_json(await dispatcher.meeting_message(team_id))
        while True:
            if await websocket.receive_text() == "ping":
                await subscriber.send_json(dispatcher.pong())
    except WebSocketDisconnect:
        pass
    finally:
        hub.remove(team_id, subscriber)
