import pytest
from fastapi import status

BASE_URL = "/teachers"


@pytest.mark.asyncio()
async def test_create_teacher(teacher_client, create_user, create_class, create_subject):
    user, _ = await create_user()
    class_ = await create_class()
    subject = await create_subject()
    data = {
        "user_id": user["id"],
        "class_ids": [class_["id"]],
        "subject_ids": [subject["id"]],
    }

    res = await teacher_client.post(BASE_URL, json=data)
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio()
async def test_get_teacher_by_id(teacher_client, create_teacher):
    teacher, _ = await create_teacher()
    res = await teacher_client.get(f"{BASE_URL}/{teacher['id']}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.asyncio()
async def test_get_teachers(admin_client, create_teacher):
    num_of_teachers = 4
    for _ in range(num_of_teachers):
        await create_teacher()
    res = await admin_client.get(BASE_URL)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == num_of_teachers


@pytest.mark.asyncio()
async def test_update_teacher(teacher_client, create_teacher, create_subject, create_class):
    teacher, _ = await create_teacher()
    class_ = await create_class()
    subject = await create_subject()

    init_res = await teacher_client.patch(f"{BASE_URL}/{teacher['id']}", json={"class_ids": [class_["id"]]})
    assert init_res.status_code == status.HTTP_200_OK
    assert len(init_res.json()["classes"]) == 1
    assert len(init_res.json()["subjects"]) == 1
    assert class_["id"] in [i["id"] for i in init_res.json()["classes"]]
    assert subject["id"] not in [i["id"] for i in init_res.json()["subjects"]]

    res = await teacher_client.patch(f"{BASE_URL}/{teacher['id']}", json={"subject_ids": [subject["id"]]})
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["classes"]) == 1
    assert len(res.json()["subjects"]) == 1
    assert class_["id"] in [i["id"] for i in res.json()["classes"]]
    assert subject["id"] in [i["id"] for i in res.json()["subjects"]]

    res = await teacher_client.patch(f"{BASE_URL}/{teacher['id']}", json={})
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["classes"]) == 1
    assert len(res.json()["subjects"]) == 1
    assert class_["id"] in [i["id"] for i in res.json()["classes"]]
    assert subject["id"] in [i["id"] for i in res.json()["subjects"]]

    res = await teacher_client.patch(
        f"{BASE_URL}/{teacher['id']}",
        json={
            "class_ids": [i["id"] for i in init_res.json()["classes"]],
            "subject_ids": [i["id"] for i in init_res.json()["subjects"]],
        },
    )
    assert res.status_code == status.HTTP_200_OK
    assert {i["id"] for i in init_res.json()["classes"]} == {i["id"] for i in res.json()["classes"]}
    assert {i["id"] for i in init_res.json()["subjects"]} == {i["id"] for i in res.json()["subjects"]}
