from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.database import get_db_session
from src.repositories.user_repo import UserRepository


async def get_db(db: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return db


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='missing_token')
    token = authorization.split(' ', 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_token') from exc
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_token_type')
    user_id = int(payload.get('sub', 0))
    user = await UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='inactive_user')
    request.state.user_id = user.id
    request.state.user_role = user.role
    return user


def require_roles(*roles: str):
    async def dependency(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='insufficient_role')
        return user

    return dependency
