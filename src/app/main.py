import logging
import asyncio
from fastapi import FastAPI
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .constants import API_TITLE, API_DESCRIPTION, API_VERSION
from .db.base import init_db, close_db, get_engine
from .redis_client import init_redis, close_redis, get_redis

from .middleware.logging_middleware import LoggingMiddleware
from .api.auth_router import router as auth_router

# Include fne package routers
from fne.api.books import router as books_router
from fne.api.authors import router as authors_router
from fne.api.users import router as users_router
from fne.api.reviews import router as reviews_router
from fne.api.comments import router as comments_router
from fne.api.likes import router as likes_router
from fne.api.orders import router as orders_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, docs_url="/docs", redoc_url="/redoc")

    # Add middleware
    app.add_middleware(LoggingMiddleware)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup
        logger.info("Starting up: init DB and Redis")
        dsn = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"
        await init_db(dsn)
        # ensure tables exist (useful for sqlite in tests)
        try:
            from .db.base import create_tables
            await create_tables()
        except Exception:
            logger.exception("Failed to create DB tables during startup")
        redis_dsn = settings.REDIS_URL or ""
        if redis_dsn:
            await init_redis(redis_dsn)
        try:
            yield
        finally:
            # shutdown
            logger.info("Shutting down: close DB and Redis")
            redis_dsn = settings.REDIS_URL or ""
            if redis_dsn:
                await close_redis()
            await close_db()

    app.router.lifespan_context = lifespan

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": API_VERSION})

    # Include routers
    app.include_router(auth_router)
    app.include_router(books_router)
    app.include_router(authors_router)
    app.include_router(users_router)
    app.include_router(reviews_router)
    app.include_router(comments_router)
    app.include_router(likes_router)
    app.include_router(orders_router)

    return app

# module-level app for uvicorn
app = create_app()
