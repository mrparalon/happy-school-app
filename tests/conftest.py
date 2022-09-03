import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator

from run import app



@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client
