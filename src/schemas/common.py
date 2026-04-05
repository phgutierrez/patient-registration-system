from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    ip_address: str | None


class HealthResponse(BaseModel):
    status: str
