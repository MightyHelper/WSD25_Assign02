from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()
_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None
_tables_initialized: bool = False

def _get_env_app_env() -> str:
    return os.environ.get('APP_ENV') or getattr(settings, 'APP_ENV', 'development')

def _get_env_database_url() -> str:
    return os.environ.get('DATABASE_URL') or getattr(settings, 'DATABASE_URL', None) or "sqlite+aiosqlite:///./dev.db"

async def init_db(dsn: str) -> None:
    global _engine, AsyncSessionLocal
    # Create engine/sessionmaker only once per process to avoid multiple engines
    if _engine is None:
        _engine = create_async_engine(dsn, future=True, echo=False)
        AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

async def create_tables() -> None:
    """Ensure DB tables exist. Do NOT drop existing data; only create missing tables.
    This avoids erasing data that tests may have inserted before app startup.
    """
    global _tables_initialized
    assert _engine is not None, "Engine not initialized"
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _tables_initialized = True

async def close_db() -> None:
    global _engine
    if _engine is not None:
        try:
            await _engine.dispose()
        except Exception as exc:
            # Some environments (notably CPython/Windows + greenlet interaction) may
            # raise unexpected exceptions during engine disposal in test shutdown.
            # Swallow exceptions to make test teardown robust and log the issue.
            logger.warning("Error while disposing DB engine during shutdown: %s", exc)

def get_engine() -> AsyncEngine | None:
    return _engine

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a database session.
    Use: async with get_session() as session:

    This will lazily initialize the engine/session maker and ensure tables exist
    so tests that call get_session() directly (outside FastAPI startup) work.
    In test env, create tables once at startup to ensure isolation.
    """
    global _engine, AsyncSessionLocal, _tables_initialized
    if AsyncSessionLocal is None:
        # lazily initialize using env DATABASE_URL or settings
        dsn = _get_env_database_url()
        await init_db(dsn)
    # In test env, ensure tables exist but avoid dropping/creating on every session
    if _get_env_app_env() == 'test' and not _tables_initialized:
        try:
            await create_tables()
        except Exception as exc:
            logger.exception("Failed to create tables during lazy init: %s", exc)
    else:
        # ensure tables exist at least once
        if _engine is not None:
            try:
                async with _engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            except Exception:
                pass
    async with AsyncSessionLocal() as session:
        yield session
