import logging
import time
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_host = request.client.host if request.client else "unknown"
        logger.info("%s - %s %s", client_host, request.method, request.url.path)
        start = time.time()
        try:
            response = await call_next(request)
            elapsed_ms = (time.time() - start) * 1000
            logger.info("%s - %s %s - %s - %.2fms", client_host, request.method, request.url.path, response.status_code, elapsed_ms)
            return response
        except Exception:
            logger.exception("Error processing request")
            raise

