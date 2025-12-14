import logging
import time
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger('app.middleware')

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_host = request.client.host if request.client else "unknown"
        path = request.url.path
        qs = f"?{request.url.query}" if request.url.query else ""
        cid = request.headers.get('X-Correlation-ID') or request.headers.get('X-Request-ID')
        logger.info("%s - %s %s%s - start (cid=%s)", client_host, request.method, path, qs, cid)
        start = time.time()
        try:
            response = await call_next(request)
            elapsed_ms = (time.time() - start) * 1000
            size = response.headers.get('content-length') or 'unknown'
            logger.info("%s - %s %s%s - %s - %s bytes - %.2fms (cid=%s)", client_host, request.method, path, qs, response.status_code, size, elapsed_ms, cid)
            return response
        except Exception as exc:
            elapsed_ms = (time.time() - start) * 1000
            logger.exception("%s - %s %s%s - ERROR after %.2fms (cid=%s): %s", client_host, request.method, path, qs, elapsed_ms, cid, exc)
            raise

