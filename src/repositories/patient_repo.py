from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.patient import Patient


class PatientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> list[Patient]:
        result = await self.db.execute(select(Patient).order_by(Patient.nome.asc()))
        return list(result.scalars().all())

    async def get(self, patient_id: int) -> Patient | None:
        result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def delete(self, patient_id: int) -> bool:
        result = await self.db.execute(delete(Patient).where(Patient.id == patient_id))
        await self.db.commit()
        return result.rowcount > 0
