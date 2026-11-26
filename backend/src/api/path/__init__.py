"""HTTP routes. Each module is a thin adapter: parse -> call a domain service -> schema."""

from fastapi import APIRouter

from src.api.path import auth, health, issues, me, meetings, rocks, scorecard, teams, todos, ws

api_router = APIRouter()
for module in (health, auth, me, teams, scorecard, issues, todos, rocks, meetings, ws):
    api_router.include_router(module.router)
