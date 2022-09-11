from datetime import datetime, timedelta

import pytest
from fastapi import status

BASE_URL = "/homeworks"


@pytest.mark.asyncio()
async def test_create_homework(
    teacher_client,
    create_subject,
    teacher,
    create_student,
    faker,
    db_client,
):
    subject = await create_subject()
    teacher_obj, _ = teacher
    students = []
    for _ in range(4):
        student, _ = await create_student()
        students.append(student)
    data = {
        "assigned_by": teacher_obj["id"],
        "assigned_to": [student["id"] for student in students],
        "subject_id": subject["id"],
        "assignment": faker.text(),
        "deadline": (datetime.utcnow() + timedelta(days=1)).astimezone().isoformat(),
    }
    res = await teacher_client.post(BASE_URL, json=data)
    assert res.status_code == status.HTTP_201_CREATED

    for homework in res.json()["data"]:
        await db_client.query(
            "delete Homework filter .id = <uuid>$homework_id",
            homework_id=homework["id"],
        )


@pytest.mark.asyncio()
async def test_create_homework_by_student(
    student_client,
    create_subject,
    teacher,
    create_student,
    faker,
):
    subject = await create_subject()
    teacher_obj, _ = teacher
    students = []
    for _ in range(4):
        student, _ = await create_student()
        students.append(student)
    data = {
        "assigned_by": teacher_obj["id"],
        "assigned_to": [student["id"] for student in students],
        "subject_id": subject["id"],
        "assignment": faker.text(),
        "deadline": (datetime.utcnow() + timedelta(days=1)).astimezone().isoformat(),
    }
    res = await student_client.post(BASE_URL, json=data)
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio()
async def test_get_homework_by_id_teacher(teacher_client, homework, create_homework, create_student, create_teacher):
    res = await teacher_client.get(f"{BASE_URL}/{homework['data'][0]['id']}")
    assert res.status_code == status.HTTP_200_OK

    other_teacher = await create_teacher()
    other_student = await create_student()
    other_teacher_homework = await create_homework(other_teacher, other_student)
    res = await teacher_client.get(f"{BASE_URL}/{other_teacher_homework['data'][0]['id']}")
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_homework_by_id_student(student_client, homework, create_teacher, create_student, create_homework):
    res = await student_client.get(f"{BASE_URL}/{homework['data'][0]['id']}")
    assert res.status_code == status.HTTP_200_OK

    other_teacher = await create_teacher()
    other_student = await create_student()
    other_teacher_homework = await create_homework(other_teacher, other_student)
    res = await student_client.get(f"{BASE_URL}/{other_teacher_homework['data'][0]['id']}")
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_homeworks(admin_client, create_homework):
    num_of_homeworks = 4
    for _ in range(4):
        await create_homework()
    res = await admin_client.get(BASE_URL)

    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()["data"]) == num_of_homeworks


@pytest.mark.asyncio()
async def test_update_homework_student(student_client, homework):
    res = await student_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"done_by_student": True},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["done_by_student"] is True

    res = await student_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"grade": 2},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = await student_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"assignment": "some"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio()
async def test_update_homework_teacher(teacher_client, homework):
    res = await teacher_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"done_by_student": True},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["done_by_student"] is True

    res = await teacher_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"grade": 2},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["grade"] == 2

    res = await teacher_client.patch(
        f"{BASE_URL}/{homework['data'][0]['id']}",
        json={"assignment": "some"},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["assignment"] == "some"
