import pytest
from fastapi import status

BASE_URL = "/parents"


@pytest.mark.asyncio()
async def test_create_parents(admin_client, create_user):
    user, _ = await create_user()
    data = {"user_id": user["id"]}
    res = await admin_client.post(BASE_URL, json=data)
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio()
async def test_get_parent_by_id(admin_client, parent):
    parent_obj, _ = parent
    res = await admin_client.get(f"{BASE_URL}/{parent_obj['id']}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.asyncio()
async def test_add_child(admin_client, create_parent, student):
    parent_obj, _ = await create_parent("@mrparalon")
    student_obj, _ = student
    res = await admin_client.post(f"{BASE_URL}/{parent_obj['id']}/children/{student_obj['id']}")
    assert res.status_code == status.HTTP_200_OK

    res = await admin_client.get(f"{BASE_URL}/{parent_obj['id']}/children")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == 1

    res = await admin_client.delete(f"{BASE_URL}/{parent_obj['id']}/children/{student_obj['id']}")
    assert res.status_code == status.HTTP_204_NO_CONTENT

    res = await admin_client.get(f"{BASE_URL}/{parent_obj['id']}/children")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == 0


@pytest.mark.asyncio()
async def test_get_parents(admin_client, create_parent):
    num_of_parents = 4
    for _ in range(num_of_parents):
        await create_parent()
    res = await admin_client.get(BASE_URL)
    assert res.status_code == status.HTTP_200_OK
