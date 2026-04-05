from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Patient Registration System API'
    environment: str = 'development'
    log_level: str = 'INFO'
    host: str = '0.0.0.0'
    port: int = 8000

    database_url: str = Field(default='postgresql+asyncpg://postgres:postgres@localhost:5432/patient_registration')
    postgres_sync_url: str | None = Field(default=None)
    redis_url: str = Field(default='redis://localhost:6379/0')

    jwt_secret_key: str = Field(default='change-me-in-production')
    jwt_algorithm: str = 'HS256'
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7

    cors_origins: str = 'http://localhost:5173'
    csrf_cookie_name: str = 'csrf_token'
    refresh_cookie_name: str = 'refresh_token'

    google_calendar_id: str = ''
    google_calendar_tz: str = 'America/Fortaleza'
    google_calendar_ics_url: str | None = None

    default_google_forms_public_id: str = '1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg'
    google_forms_public_id: str | None = None
    google_forms_viewform_url: str | None = None
    google_forms_timeout: int = 10

    sqlite_legacy_path: str = str(Path('instance') / 'prontuario.db')

    @property
    def parsed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]

    @property
    def effective_postgres_sync_url(self) -> str:
        if self.postgres_sync_url:
            return self.postgres_sync_url
        if self.database_url.startswith('postgresql+asyncpg://'):
            return self.database_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://', 1)
        if self.database_url.startswith('postgresql://'):
            return self.database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
