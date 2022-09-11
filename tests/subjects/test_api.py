import pytest
from faker import Faker
from fastapi import status

BASE_URL = "/subjects"


@pytest.mark.asyncio()
async def test_create_subject(teacher_client, db_client):
    res = await teacher_client.post(BASE_URL, json={"name": "Математика"})
    assert res.status_code == status.HTTP_201_CREATED
    await db_client.query(
        "delete Subject filter .id = <uuid>$subject_id",
        subject_id=res.json()["id"],
    )


@pytest.mark.asyncio()
async def test_get_subject_by_id(teacher_client, create_subject):
    subject = await create_subject()
    res = await teacher_client.get(f"{BASE_URL}/{subject['id']}")
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.asyncio()
async def test_get_subjects(admin_client, create_subject, faker: Faker):
    number_of_subjects = 3
    for _ in range(number_of_subjects):
        await create_subject(faker.word())
    res = await admin_client.get(BASE_URL)
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == number_of_subjects
