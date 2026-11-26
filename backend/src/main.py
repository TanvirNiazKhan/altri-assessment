"""Application factory. `uvicorn src.main:app`; tests call `create_app(settings, clock)`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middlewares.error_handler import register_exception_handlers
from src.api.middlewares.request_id import RequestIdMiddleware
from src.api.path import api_router
from src.api.realtime.dispatcher import TeamEventDispatcher
from src.config.database import build_engine, build_sessionmaker
from src.config.logging import configure_logging
from src.config.settings import Settings, get_settings
from src.domain.shared.clock import Clock
from src.infra.adapters.session_signer import SessionSigner
from src.infra.realtime.hub import ConnectionHub
from src.infra.realtime.listener import PgListener, asyncpg_dsn
from src.infra.services.clock import build_clock


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings)
        app.state.engine = engine
        app.state.sessionmaker = build_sessionmaker(engine)
        app.state.hub = ConnectionHub()
        app.state.dispatcher = TeamEventDispatcher(
            app.state.hub, app.state.sessionmaker, app.state.clock
        )
        listener = PgListener(
            asyncpg_dsn(settings.database_url),
            on_event=app.state.dispatcher.handle,
            on_reconnect=app.state.dispatcher.resync_all,
        )
        if settings.realtime_enabled:
            await listener.start()
        app.state.listener = listener
        try:
            yield
        finally:
            await listener.stop()
            await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    app.state.clock = clock or build_clock(settings.app_now, settings.app_clock_mode)
    app.state.session_signer = SessionSigner(settings.session_secret, settings.session_max_age_s)

    register_exception_handlers(app)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
