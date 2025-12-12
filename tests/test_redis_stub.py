import asyncio

from app.redis_client import get_redis, _NullRedis, RedisLike


def test_nullredis_implements_protocol():
    r = get_redis()
    assert isinstance(r, RedisLike)


async def _async_use_redis(r):
    assert await r.get("somekey") is None
    assert await r.set("k", "v") is True
    assert await r.delete("k") == 0


def test_nullredis_async_methods():
    r = get_redis()
    # run async usage
    asyncio.run(_async_use_redis(r))

