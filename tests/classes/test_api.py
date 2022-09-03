import pytest
from fastapi import status

BASE_URL = "/classes"

@pytest.mark.asyncio
async def test_create_class(client):
    res = await client.get(f"{BASE_URL}")
    assert res.status_code == status.HTTP_200_OK
