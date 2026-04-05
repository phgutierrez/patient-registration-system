from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.deps import get_db, require_roles
from src.repositories.patient_repo import PatientRepository
from src.schemas.surgery import SurgeryRequestCreate, SurgeryRequestRead
from src.services.forms_service import FormsService
from src.services.pdf_service import PdfService
from src.services.surgery_service import SurgeryService

router = APIRouter()


@router.get('', response_model=list[SurgeryRequestRead])
async def list_surgeries(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    return await SurgeryService(db).list()


@router.post('', response_model=SurgeryRequestRead)
async def create_surgery(
    payload: SurgeryRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles('admin', 'medico')),
):
    surgery_service = SurgeryService(db)
    surgery = await surgery_service.create(payload)

    patient = await PatientRepository(db).get(surgery.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='patient_not_found')

    pdf_service = PdfService()
    surgery.pdf_filename = await pdf_service.generate_internacao_pdf(patient, surgery, current_user)
    surgery.pdf_hemocomponente = await pdf_service.generate_hemocomponente_pdf(patient, surgery)
    await surgery_service.save(surgery)
    return surgery


@router.get('/{surgery_id}', response_model=SurgeryRequestRead)
async def get_surgery(
    surgery_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    surgery = await SurgeryService(db).get(surgery_id)
    if not surgery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='surgery_not_found')
    return surgery


@router.get('/{surgery_id}/pdf')
async def download_internacao_pdf(
    surgery_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    surgery = await SurgeryService(db).get(surgery_id)
    if not surgery or not surgery.pdf_filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='pdf_not_found')
    file_path = Path('src/static/preenchidos') / surgery.pdf_filename
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='pdf_file_missing')
    return FileResponse(file_path, filename=surgery.pdf_filename, media_type='application/pdf')


@router.get('/{surgery_id}/pdf-hemocomponente')
async def download_hemocomponente_pdf(
    surgery_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    surgery = await SurgeryService(db).get(surgery_id)
    if not surgery or not surgery.pdf_hemocomponente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='pdf_hemocomponente_not_found')
    file_path = Path('src/static/preenchidos') / surgery.pdf_hemocomponente
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='pdf_file_missing')
    return FileResponse(file_path, filename=surgery.pdf_hemocomponente, media_type='application/pdf')


@router.get('/{surgery_id}/schedule/preview')
async def schedule_preview(
    surgery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    surgery = await SurgeryService(db).get(surgery_id)
    if not surgery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='surgery_not_found')

    patient = await PatientRepository(db).get(surgery.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='patient_not_found')

    forms = FormsService(get_settings())
    payload = forms.build_forms_payload(surgery, patient, current_user.full_name)
    return {
        'ok': True,
        'preview': forms.build_preview(payload),
        'already_scheduled': surgery.calendar_status == 'agendado',
        'scheduled_at': surgery.scheduled_at,
        'event_link': surgery.scheduled_event_link,
    }


@router.post('/{surgery_id}/schedule/confirm')
async def schedule_confirm(
    surgery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles('admin', 'medico')),
):
    surgery_service = SurgeryService(db)
    surgery = await surgery_service.get(surgery_id)
    if not surgery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='surgery_not_found')

    if surgery.calendar_status == 'agendado':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='already_scheduled')

    patient = await PatientRepository(db).get(surgery.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='patient_not_found')

    forms = FormsService(get_settings())
    payload = forms.build_forms_payload(surgery, patient, current_user.full_name)
    success, message, status_code = forms.submit_form(payload)

    if not success:
        surgery.calendar_status = 'erro'
        await surgery_service.save(surgery)
        raise HTTPException(status_code=502 if status_code in {400, 403, 404, 502, 504} else 500, detail=message)

    surgery.calendar_status = 'agendado'
    surgery.scheduled_at = datetime.utcnow()
    surgery.scheduled_event_link = None
    await surgery_service.save(surgery)

    return {
        'ok': True,
        'message': message,
        'scheduled_at': surgery.scheduled_at,
    }
