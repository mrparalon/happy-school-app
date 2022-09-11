import asyncio
import random
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import MagicMock

import edgedb
import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient
from pytest_mock import MockerFixture
from telethon import TelegramClient
from telethon.types import User as TgUser

import app.api.v1.auth.auth as auth_dependencies
from run import app


@pytest.fixture(autouse=True)
def _mock_auth_functions(mocker: MockerFixture):
    mocker.patch.object(
        auth_dependencies,
        "get_password_hash",
        MagicMock(return_value="mocked_hash"),
    )


async def mock_tg_user(*args, **kwargs):  # noqa: ARG001
    return TgUser(id=random.randint(100, 30000))


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def faker_seed():
    return random.randint(0, 10000)


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        # await tg_client.connect() # noqa: ERA001
        # await tg_client.sign_in(bot_token=settings.BOT_TOKEN) # noqa: ERA001
        yield client


@pytest_asyncio.fixture()
async def db_client():
    async with edgedb.asyncio_client.create_async_client() as db:
        yield db
        await db.query(
            """
            delete Class;
            delete Homework;
            delete Subject;
            delete User;
            """
        )


@pytest_asyncio.fixture()
async def create_user(client, faker: Faker, mocker: MockerFixture):
    async def inner(tg_name: str | None = None):
        mocker.patch.object(TelegramClient, "get_entity", mock_tg_user)
        password = faker.password()
        profile = faker.profile()
        username = profile["username"]
        resp = await client.post(
            "/users",
            data={
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "username": username,
                "password": password,
                "tg_name": tg_name,
            },
        )
        return resp.json(), password

    yield inner


@pytest_asyncio.fixture()
async def admin_client(client, create_user, db_client):
    user, password = await create_user()
    await db_client.query(
        """
            INSERT Admin {
                user := (select User filter .id = <uuid>$user_id),
                }
            """,
        user_id=user["id"],
    )
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        res = (
            await client.post(
                "/token",
                data={"username": user["username"], "password": password},
            )
        ).json()
        client.headers.update({"Authorization": f"{res['token_type'].capitalize()} {res['access_token']}"})
        yield client


@pytest_asyncio.fixture()
async def create_class(admin_client):
    async def inner(year: int = 1):
        res = (await admin_client.post("/classes", json={"name": "name", "year": year})).json()
        return res

    yield inner


@pytest_asyncio.fixture()
async def create_student(admin_client, create_user, create_class):
    async def inner(year: int = 1):
        user, password = await create_user()
        class_ = await create_class(year)
        res = (
            await admin_client.post(
                "/students",
                json={"user_id": user["id"], "class_id": class_["id"]},
            )
        ).json()
        return res, password

    return inner


@pytest_asyncio.fixture()
async def create_parent(admin_client, create_user):
    async def inner(tg_name: str | None = None):
        user, password = await create_user(tg_name)
        res = (
            await admin_client.post(
                "/parents",
                json={"user_id": user["id"]},
            )
        ).json()
        return res, password

    return inner


@pytest_asyncio.fixture()
async def student(create_student):
    return await create_student()


@pytest_asyncio.fixture()
async def parent(create_parent):
    return await create_parent()


@pytest_asyncio.fixture()
async def teacher(create_teacher):
    return await create_teacher()


@pytest_asyncio.fixture()
async def teacher_client(teacher):
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        user, password = teacher
        res = (
            await client.post(
                "/token",
                data={
                    "username": user["user"]["username"],
                    "password": password,
                },
            )
        ).json()
        client.headers.update({"Authorization": f"{res['token_type'].capitalize()} {res['access_token']}"})
        yield client


@pytest_asyncio.fixture()
async def create_subject(admin_client, faker):
    async def inner(name: str | None = None):
        if name is None:
            name = faker.word()
        res = (await admin_client.post("/subjects", json={"name": name})).json()
        return res

    yield inner


@pytest_asyncio.fixture()
async def create_teacher(client, create_user, create_class, create_subject, faker):
    async def inner():
        user, password = await create_user()
        class_ = await create_class()
        subject = await create_subject(faker.word())
        res = (
            await client.post(
                "/teachers",
                json={
                    "user_id": user["id"],
                    "class_ids": [class_["id"]],
                    "subject_ids": [subject["id"]],
                },
            )
        ).json()
        return res, password

    return inner


@pytest_asyncio.fixture()
async def student_client(student):
    student_obj, password = student

    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        res = (
            await client.post(
                "/token",
                data={
                    "username": student_obj["user"]["username"],
                    "password": password,
                },
            )
        ).json()
        client.headers.update({"Authorization": f"{res['token_type'].capitalize()} {res['access_token']}"})
        yield client


@pytest_asyncio.fixture()
async def create_homework(teacher_client, create_subject, teacher, student, faker):
    async def inner(teacher=teacher, student=student):
        subject = await create_subject()
        teacher_obj, _ = teacher
        student_obj, _ = student
        students = [student_obj["id"]]
        data = {
            "assigned_by": teacher_obj["id"],
            "assigned_to": students,
            "subject_id": subject["id"],
            "assignment": faker.text(),
            "deadline": (datetime.utcnow() + timedelta(days=1)).astimezone().isoformat(),
        }
        res = (await teacher_client.post("/homeworks", json=data)).json()
        return res

    yield inner


@pytest_asyncio.fixture()
async def homework(create_homework):
    return await create_homework()
