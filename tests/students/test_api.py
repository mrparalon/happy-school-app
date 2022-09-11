import pytest
from fastapi import status

BASE_URL = "/students"


@pytest.mark.asyncio()
async def test_create_student(admin_client, create_user, create_class):
    user, _ = await create_user()
    class_ = await create_class()
    data = {"user_id": user["id"], "class_id": class_["id"]}
    res = await admin_client.post(BASE_URL, json=data)
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio()
async def test_get_student_by_id(admin_client, create_student):
    student, _ = await create_student()
    res = await admin_client.get(f"{BASE_URL}/{student['id']}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.asyncio()
async def test_get_students(admin_client, create_student):
    num_of_students = 4
    for _ in range(num_of_students):
        await create_student()
    res = await admin_client.get(BASE_URL)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == num_of_students


@pytest.mark.asyncio()
async def test_update_student_class(admin_client, create_student, create_class):
    student, _ = await create_student()
    class_ = await create_class()
    res = await admin_client.patch(f"{BASE_URL}/{student['id']}", json={"class_id": class_["id"]})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["class"]["id"] == class_["id"]
