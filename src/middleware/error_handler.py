import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception('unhandled_exception', path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={'detail': 'internal_server_error'})
