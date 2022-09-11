import pytest
from fastapi import status

BASE_URL = "/classes"


@pytest.mark.asyncio()
async def test_create_class(teacher_client, db_client):
    res = await teacher_client.post(BASE_URL, json={"name": "7a", "year": 7})
    assert res.status_code == status.HTTP_201_CREATED
    await db_client.query("delete Class filter .id = <uuid>$class_id", class_id=res.json()["id"])


@pytest.mark.asyncio()
async def test_get_class_by_id(teacher_client, create_class):
    class_ = await create_class()
    res = await teacher_client.get(f"{BASE_URL}/{class_['id']}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.asyncio()
async def test_get_classes(admin_client, create_class):
    number_of_classes = 3
    for _ in range(number_of_classes):
        await create_class()
    res = await admin_client.get(BASE_URL)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == number_of_classes
