from prometheus_client import Counter, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import PLATFORM_COLLECTOR, PROCESS_COLLECTOR, GC_COLLECTOR
from starlette.responses import Response

# Default registry used by the app; tests can replace it via set_registry
_registry: CollectorRegistry = CollectorRegistry()
_registry.register(GC_COLLECTOR)
_registry.register(PROCESS_COLLECTOR)
_registry.register(PLATFORM_COLLECTOR)
# Labeled counter for redis cache hit/miss
_redis_hitrate = Counter(
    "app_cache_redis_hitrate_total",
    "Redis cache hitrate counts by result and cache",
    labelnames=("result", "cache"),
    registry=_registry,
)


def set_registry(registry: CollectorRegistry) -> None:
    """Replace the module registry (useful for tests).
    This re-creates the redis hitrate counter registered to the provided registry.
    """
    global _registry, _redis_hitrate
    _registry = registry
    _redis_hitrate = Counter(
        "app_cache_redis_hitrate_total",
        "Redis cache hitrate counts by result and cache",
        labelnames=("result", "cache"),
        registry=_registry,
    )


def get_registry() -> CollectorRegistry:
    return _registry


def inc_redis_hitrate(result: str, cache_name: str = "redis") -> None:
    """Increment the redis hitrate counter with result in ("hit","miss","error")
    """
    try:
        _redis_hitrate.labels(result=result, cache=cache_name).inc()
    except Exception:
        # Metrics should never crash the application; ignore errors
        return


def metrics_response() -> Response:
    """Return a Starlette Response with the latest metrics for mounting at /metrics."""
    data = generate_latest(_registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

