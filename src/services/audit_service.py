from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog
from src.repositories.audit_repo import AuditRepository


class AuditService:
    def __init__(self, db: AsyncSession):
        self.repo = AuditRepository(db)

    async def log(self, *, user_id: int | None, action: str, entity_type: str, entity_id: str | None, old_values: dict | None, new_values: dict | None, ip_address: str | None):
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
        )
        return await self.repo.create(entry)

    async def list_recent(self, limit: int = 100):
        return await self.repo.list_recent(limit=limit)
