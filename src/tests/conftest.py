import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/15'
os.environ['JWT_SECRET_KEY'] = 'test-secret'

from src.core.cache import cache
from src.core.security import hash_password
from src.database import get_db_session
from src.main import app
from src.models import Base
from src.models.user import User


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture()
async def client():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    testing_session_local = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    async with testing_session_local() as session:
        session.add(User(username='admin', password_hash=hash_password('admin123'), role='admin', full_name='Admin Test', is_active=True))
        await session.commit()

    class InMemoryCache:
        store = {}

        async def set(self, key, value, ex=None):
            self.store[key] = value

        async def get(self, key):
            return self.store.get(key)

        async def delete(self, key):
            self.store.pop(key, None)

    cache._client = InMemoryCache()  # type: ignore[attr-defined]

    async with AsyncClient(transport=ASGITransport(app=app, lifespan='off'), base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
