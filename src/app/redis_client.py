import redis.asyncio as aioredis
from typing import Optional, Any, Protocol, runtime_checkable
from .config import settings

_redis: Optional[aioredis.Redis] = None


@runtime_checkable
class RedisLike(Protocol):
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any, ex: int | None = None) -> bool: ...
    async def delete(self, *keys: str) -> int: ...


class _NullRedis(RedisLike):
    """A lightweight async-compatible Redis stub used when Redis isn't configured.
    Methods mimic the aioredis.Redis async API used by the app: get, set, delete.
    """
    async def get(self, key: str) -> Any:
        return None

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        return True

    async def delete(self, *keys: str) -> int:
        return 0


async def init_redis(dsn: str) -> None:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(dsn, encoding="utf-8", decode_responses=True)

async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


def get_redis() -> RedisLike:
    """Return the initialized redis client or a null-implementation when none.
    This keeps handlers simple and avoids crashing when REDIS_URL is not provided
    (for tests/local dev).
    """
    if _redis is None:
        return _NullRedis()
    return _redis

# FastAPI dependency
def get_redis_dep() -> RedisLike:
    return get_redis()
