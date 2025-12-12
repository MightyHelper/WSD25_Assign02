import redis.asyncio as aioredis
from typing import Optional
from .config import settings

_redis: Optional[aioredis.Redis] = None

async def init_redis(dsn: str) -> None:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(dsn, encoding="utf-8", decode_responses=True)

async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None

def get_redis() -> aioredis.Redis:
    assert _redis is not None, "Redis client not initialized"
    return _redis

