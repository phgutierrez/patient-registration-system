from datetime import date

from fastapi import APIRouter, Depends, Query

from src.core.deps import require_roles
from src.services.calendar_service import CalendarFacade

router = APIRouter()


@router.get('/events')
async def list_events(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    _user=Depends(require_roles('admin', 'medico', 'enfermeiro')),
):
    return await CalendarFacade().list_events(start=start, end=end)
