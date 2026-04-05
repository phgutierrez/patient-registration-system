from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import get_current_user, get_db, require_roles
from src.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from src.services.patient_service import PatientService

router = APIRouter()


@router.get('', response_model=list[PatientRead])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await PatientService(db).list()


@router.post('', response_model=PatientRead)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    return await PatientService(db).create(payload)


@router.put('/{patient_id}', response_model=PatientRead)
async def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico')),
):
    patient = await PatientService(db).update(patient_id, payload)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='patient_not_found')
    return patient


@router.delete('/{patient_id}', status_code=204)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin')),
):
    ok = await PatientService(db).delete(patient_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='patient_not_found')
