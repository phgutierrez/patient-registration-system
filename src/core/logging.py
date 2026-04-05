import logging
import sys
import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging(log_level: str = 'INFO') -> None:
    timestamper = structlog.processors.TimeStamper(fmt='iso', utc=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format='%(message)s', stream=sys.stdout, level=getattr(logging, log_level.upper(), logging.INFO))


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('x-request-id', str(uuid.uuid4()))
        started = time.perf_counter()
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path, method=request.method)
        request.state.request_id = request_id
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        response.headers['x-request-id'] = request_id
        structlog.get_logger().info('request_completed', status=response.status_code, latency_ms=latency_ms)
        structlog.contextvars.clear_contextvars()
        return response
