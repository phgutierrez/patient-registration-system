from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis

from src.core.config import get_settings


class RedisCache:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = redis.from_url(settings.redis_url, decode_responses=True)
        await self._client.ping()

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError('Redis not initialized')
        return self._client

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    @asynccontextmanager
    async def lock(self, key: str, timeout: int = 10):
        lock = self.client.lock(key, timeout=timeout)
        await lock.acquire()
        try:
            yield
        finally:
            if lock.locked():
                await lock.release()


cache = RedisCache()
