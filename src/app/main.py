import logging
import asyncio
from fastapi import FastAPI
from starlette.responses import JSONResponse

from .config import settings
from .constants import API_TITLE, API_DESCRIPTION, API_VERSION
from .db.base import init_db, close_db, get_engine
from .redis_client import init_redis, close_redis, get_redis

from .middleware.logging_middleware import LoggingMiddleware
from .api.auth_router import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, docs_url="/docs", redoc_url="/redoc")

    # Add middleware
    app.add_middleware(LoggingMiddleware)

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("Starting up: init DB and Redis")
        await init_db(settings.DATABASE_URL)
        await init_redis(settings.REDIS_URL)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("Shutting down: close DB and Redis")
        await close_redis()
        await close_db()

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": API_VERSION})

    # Include routers
    app.include_router(auth_router)

    return app

# module-level app for uvicorn
app = create_app()
