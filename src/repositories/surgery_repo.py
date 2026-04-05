from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.surgery_request import SurgeryRequest


class SurgeryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> list[SurgeryRequest]:
        result = await self.db.execute(select(SurgeryRequest).order_by(SurgeryRequest.created_at.desc()))
        return list(result.scalars().all())

    async def get(self, surgery_id: int) -> SurgeryRequest | None:
        result = await self.db.execute(select(SurgeryRequest).where(SurgeryRequest.id == surgery_id))
        return result.scalar_one_or_none()

    async def create(self, surgery: SurgeryRequest) -> SurgeryRequest:
        self.db.add(surgery)
        await self.db.commit()
        await self.db.refresh(surgery)
        return surgery

    async def save(self, surgery: SurgeryRequest) -> SurgeryRequest:
        await self.db.commit()
        await self.db.refresh(surgery)
        return surgery
