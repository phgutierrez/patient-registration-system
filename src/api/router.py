from fastapi import APIRouter

from src.api.routes import audit, auth, calendar, health, patients, surgery

api_router = APIRouter(prefix='/api')
api_router.include_router(health.router, tags=['health'])
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(patients.router, prefix='/patients', tags=['patients'])
api_router.include_router(surgery.router, prefix='/surgery', tags=['surgery'])
api_router.include_router(calendar.router, prefix='/calendar', tags=['calendar'])
api_router.include_router(audit.router, prefix='/audit', tags=['audit'])
