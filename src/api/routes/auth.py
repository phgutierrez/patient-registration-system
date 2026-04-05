from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.deps import get_current_user
from src.core.security import decode_token
from src.database import get_db_session
from src.schemas.auth import LoginRequest, TokenResponse, UserMe
from src.services.auth_service import AuthService

router = APIRouter()


def _set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    settings = get_settings()
    response.set_cookie(settings.refresh_cookie_name, refresh_token, httponly=True, secure=False, samesite='lax', path='/api/auth')
    response.set_cookie(settings.csrf_cookie_name, csrf_token, httponly=False, secure=False, samesite='lax', path='/api/auth')


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.refresh_cookie_name, path='/api/auth')
    response.delete_cookie(settings.csrf_cookie_name, path='/api/auth')


def _validate_csrf(request: Request) -> None:
    settings = get_settings()
    header = request.headers.get('x-csrf-token')
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not header or not cookie or header != cookie:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='csrf_invalid')


def _decode_or_401(token: str) -> dict:
    try:
        return decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid_token') from exc


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    user = await service.authenticate(payload.username, payload.password)
    access, refresh, csrf = await service.issue_tokens(user)
    _set_auth_cookies(response, refresh, csrf)
    settings = get_settings()
    return TokenResponse(access_token=access, expires_in=settings.jwt_access_ttl_min * 60)


@router.post('/refresh', response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    _validate_csrf(request)
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='missing_refresh_cookie')
    payload = _decode_or_401(refresh_token)
    service = AuthService(db)
    access, new_refresh, csrf = await service.rotate_refresh(payload)
    _set_auth_cookies(response, new_refresh, csrf)
    return TokenResponse(access_token=access, expires_in=settings.jwt_access_ttl_min * 60)


@router.post('/logout', status_code=204)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    _validate_csrf(request)
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if refresh_token:
        payload = _decode_or_401(refresh_token)
        await AuthService(db).revoke(payload)
    _clear_auth_cookies(response)


@router.get('/me', response_model=UserMe)
async def me(user=Depends(get_current_user)):
    return UserMe(id=user.id, username=user.username, full_name=user.full_name, role=user.role)
