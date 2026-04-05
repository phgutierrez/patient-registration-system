from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from src.api.router import api_router
from src.core.cache import cache
from src.core.config import get_settings
from src.core.logging import RequestContextMiddleware, configure_logging
from src.database import SessionLocal
from src.middleware.audit_middleware import AuditMiddleware
from src.middleware.error_handler import unhandled_exception_handler
from src.services.auth_service import seed_admin_if_needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    await cache.connect()
    async with SessionLocal() as session:
        await session.execute(text('SELECT 1'))
        await seed_admin_if_needed(session)
    yield
    await cache.close()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['*'],
)
app.add_exception_handler(Exception, unhandled_exception_handler)

web_dist = Path('web/dist')
if web_dist.exists():
    app.mount('/assets', StaticFiles(directory=str(web_dist / 'assets')), name='assets')


@app.get('/{full_path:path}', include_in_schema=False)
async def spa_fallback(full_path: str):
    index_file = Path('web/dist/index.html')
    if index_file.exists():
        return FileResponse(index_file)
    return {'message': 'Frontend build not found', 'path': full_path}
