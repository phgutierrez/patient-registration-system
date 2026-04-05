from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.deps import get_db, require_roles
from src.services.audit_service import AuditService

router = APIRouter()


@router.get('')
async def list_audit(limit: int = 100, db: AsyncSession = Depends(get_db), _user=Depends(require_roles('admin'))):
    entries = await AuditService(db).list_recent(limit=limit)
    return [
        {
            'id': entry.id,
            'user_id': entry.user_id,
            'action': entry.action,
            'entity_type': entry.entity_type,
            'entity_id': entry.entity_id,
            'ip_address': entry.ip_address,
            'created_at': entry.created_at,
        }
        for entry in entries
    ]
