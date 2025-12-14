import logging
import logging.config
import os
from fastapi import FastAPI
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .constants import API_TITLE, API_DESCRIPTION, API_VERSION
from app.db.base import init_db, close_db, create_tables
from .redis_client import init_redis, close_redis

from .middleware.logging_middleware import LoggingMiddleware
from .api.auth_router import router as auth_router

# Include app package routers
from app.api.books import router as books_router
from app.api.authors import router as authors_router
from app.api.users import router as users_router
from app.api.reviews import router as reviews_router
from app.api.comments import router as comments_router
from app.api.likes import router as likes_router
from app.api.orders import router as orders_router


def configure_logging():
    """Load logging configuration from YAML file specified in LOGGING_CONFIG env or default package file.
    Falls back to a reasonable basicConfig if loading fails.
    """
    try:
        import yaml
    except Exception:
        logging.basicConfig(level=logging.INFO)
        return

    cfg_path = os.environ.get('LOGGING_CONFIG')
    if not cfg_path:
        cfg_path = os.path.join(os.path.dirname(__file__), 'logging.yaml')
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'rt', encoding='utf-8') as fh:
                cfg = yaml.safe_load(fh)
            # If file contains a path for file handlers, ensure directories exist
            # Walk handlers to find filenames
            handlers = cfg.get('handlers', {}) if isinstance(cfg, dict) else {}
            for h in handlers.values():
                fname = h.get('filename') if isinstance(h, dict) else None
                if fname:
                    d = os.path.dirname(fname)
                    if d and not os.path.exists(d):
                        try:
                            os.makedirs(d, exist_ok=True)
                        except Exception:
                            pass
            logging.config.dictConfig(cfg)
            return
    except Exception:
        # If any error occurs parsing/applying YAML, fall back to basicConfig
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).exception('Failed to load logging configuration from %s', cfg_path)
        return

    # final fallback
    logging.basicConfig(level=logging.INFO)


# Configure logging as early as possible
configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, docs_url="/docs", redoc_url="/redoc")

    # Add middleware
    app.add_middleware(LoggingMiddleware)

    # Global exception handler with helpful JSON in non-production
    @app.exception_handler(Exception)
    async def all_exception_handler(request, exc):
        # Log full traceback server-side
        logger.exception("Unhandled exception during request: %s", exc)
        if getattr(settings, 'APP_ENV', 'development') != 'production':
            # Provide type and message to aid debugging in tests/dev
            return JSONResponse(status_code=500, content={"detail": str(exc), "type": exc.__class__.__name__})
        # Generic message in production
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup
        logger.info("Starting up: init DB and Redis")
        # Default to in-memory sqlite if no DATABASE_URL provided
        dsn = settings.DATABASE_URL or "sqlite+aiosqlite://"
        await init_db(dsn)
        # ensure tables exist (useful for sqlite in tests)
        try:
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

    # noinspection PyUnresolvedReferences
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

# Note: do not create app at import time to avoid side-effects during test collection.
# If running via uvicorn, use `uvicorn app.main:create_app` or create app explicitly.
