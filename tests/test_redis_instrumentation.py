import pytest
from prometheus_client import CollectorRegistry

from app import redis_client, metrics


class DummyClient:
    def __init__(self, value):
        self._value = value
    async def get(self, key: str):
        return self._value


@pytest.mark.asyncio
async def test_redis_get_hits_and_misses():
    reg = CollectorRegistry()
    metrics.set_registry(reg)

    # simulate miss
    client_miss = DummyClient(None)
    instr = redis_client._InstrumentedRedis(client_miss)
    val = await instr.get("somekey")
    assert val is None
    out = metrics.metrics_response().body.decode('utf-8')
    assert 'result="miss"' in out

    # simulate hit
    client_hit = DummyClient("value")
    instr2 = redis_client._InstrumentedRedis(client_hit)
    val2 = await instr2.get("somekey")
    assert val2 == "value"
    out2 = metrics.metrics_response().body.decode('utf-8')
    assert 'result="hit"' in out2

