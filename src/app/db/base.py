from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()
_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None

async def init_db(dsn: str) -> None:
    global _engine, AsyncSessionLocal
    if _engine is None:
        _engine = create_async_engine(dsn, future=True, echo=False)
        AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

async def create_tables() -> None:
    """Create DB tables (runs Base.metadata.create_all) using the async engine."""
    assert _engine is not None, "Engine not initialized"
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    """
    assert AsyncSessionLocal is not None, "Session maker not initialized"
    async with AsyncSessionLocal() as session:
        yield session
