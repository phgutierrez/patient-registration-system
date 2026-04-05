from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.database import SessionLocal
from src.services.audit_service import AuditService


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/api') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            async with SessionLocal() as session:
                service = AuditService(session)
                user_id = getattr(request.state, 'user_id', None)
                await service.log(
                    user_id=user_id,
                    action=request.method,
                    entity_type=request.url.path,
                    entity_id=None,
                    old_values=None,
                    new_values=None,
                    ip_address=request.client.host if request.client else None,
                )
        return response
