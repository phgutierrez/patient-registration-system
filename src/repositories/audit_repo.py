from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        result = await self.db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def create(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
