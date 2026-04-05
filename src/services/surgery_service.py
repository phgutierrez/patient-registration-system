from sqlalchemy.ext.asyncio import AsyncSession

from src.models.surgery_request import SurgeryRequest
from src.repositories.surgery_repo import SurgeryRepository
from src.schemas.surgery import SurgeryRequestCreate


class SurgeryService:
    def __init__(self, db: AsyncSession):
        self.repo = SurgeryRepository(db)

    async def list(self):
        return await self.repo.list()

    async def get(self, surgery_id: int):
        return await self.repo.get(surgery_id)

    async def create(self, data: SurgeryRequestCreate):
        surgery = SurgeryRequest(**data.model_dump())
        return await self.repo.create(surgery)

    async def save(self, surgery: SurgeryRequest):
        return await self.repo.save(surgery)
