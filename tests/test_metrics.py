import pytest
from prometheus_client import CollectorRegistry

from app import metrics


def test_counter_increments():
    reg = CollectorRegistry()
    metrics.set_registry(reg)

    # initial value should be zero (no samples yet)
    metrics.inc_redis_hitrate("hit")
    metrics.inc_redis_hitrate("miss")
    # generate metrics output and assert the lines exist
    data = metrics.metrics_response().body.decode('utf-8')
    assert 'app_cache_redis_hitrate_total' in data
    assert 'result="hit"' in data
    assert 'result="miss"' in data


def test_set_registry_rebinds_counter():
    reg1 = CollectorRegistry()
    metrics.set_registry(reg1)
    metrics.inc_redis_hitrate("hit")
    out1 = metrics.metrics_response().body.decode('utf-8')
    assert 'result="hit"' in out1

    reg2 = CollectorRegistry()
    metrics.set_registry(reg2)
    out2 = metrics.metrics_response().body.decode('utf-8')
    # After swapping registry, previous metric should not be present in new registry
    assert 'result="hit"' not in out2

