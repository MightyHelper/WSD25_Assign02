from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

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
        await _engine.dispose()

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
