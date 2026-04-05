from sqlalchemy.ext.asyncio import AsyncSession

from src.models.patient import Patient
from src.repositories.patient_repo import PatientRepository
from src.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PatientRepository(db)

    async def list(self):
        return await self.repo.list()

    async def create(self, data: PatientCreate):
        patient = Patient(**data.model_dump())
        return await self.repo.create(patient)

    async def update(self, patient_id: int, data: PatientUpdate):
        patient = await self.repo.get(patient_id)
        if not patient:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def delete(self, patient_id: int) -> bool:
        return await self.repo.delete(patient_id)
