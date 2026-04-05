from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache
from src.core.config import get_settings
from src.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> User:
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_credentials')
        return user

    async def issue_tokens(self, user: User) -> tuple[str, str, str]:
        settings = get_settings()
        jti = uuid4().hex
        access = create_access_token(user.id, user.role)
        refresh = create_refresh_token(user.id, user.role, jti)
        expires = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_days)
        self.db.add(RefreshToken(id=jti, user_id=user.id, expires_at=expires))
        await self.db.commit()
        await cache.set(f'refresh:{jti}', str(user.id), ex=settings.jwt_refresh_ttl_days * 86400)
        csrf = uuid4().hex
        return access, refresh, csrf

    async def rotate_refresh(self, refresh_payload: dict) -> tuple[str, str, str]:
        settings = get_settings()
        if refresh_payload.get('type') != 'refresh':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_refresh_token')
        old_jti = refresh_payload.get('jti')
        if not old_jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_refresh_token')
        if not await cache.get(f'refresh:{old_jti}'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='revoked_refresh_token')

        user_id = int(refresh_payload['sub'])
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='inactive_user')

        await cache.delete(f'refresh:{old_jti}')
        await self.db.execute(delete(RefreshToken).where(RefreshToken.id == old_jti))
        await self.db.commit()
        return await self.issue_tokens(user)

    async def revoke(self, refresh_payload: dict) -> None:
        jti = refresh_payload.get('jti')
        if not jti:
            return
        await cache.delete(f'refresh:{jti}')
        await self.db.execute(delete(RefreshToken).where(RefreshToken.id == jti))
        await self.db.commit()


async def seed_admin_if_needed(db: AsyncSession) -> None:
    existing_user = await db.execute(select(User.id).limit(1))
    if existing_user.scalar_one_or_none() is not None:
        return

    db.add(User(username='admin', password_hash=hash_password('admin123'), role='admin', full_name='Administrador', is_active=True))
    await db.commit()
