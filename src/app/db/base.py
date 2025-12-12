from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional

Base = declarative_base()
_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None

async def init_db(dsn: str) -> None:
    global _engine, AsyncSessionLocal
    if _engine is None:
        _engine = create_async_engine(dsn, future=True, echo=False)
        AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()

def get_engine() -> AsyncEngine | None:
    return _engine

async def get_session() -> AsyncSession:
    """Dependency-style session provider for routes.
    Use: async with get_session() as session:
    """
    assert AsyncSessionLocal is not None, "Session maker not initialized"
    async with AsyncSessionLocal() as session:
        yield session

