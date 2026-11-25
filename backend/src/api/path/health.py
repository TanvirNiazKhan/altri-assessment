from fastapi import APIRouter
from sqlalchemy import text

from src.config.dependency import DbSessionDep

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness (database reachable)")
async def ready(session: DbSessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
