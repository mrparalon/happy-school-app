from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import orjson
from edgedb.asyncio_client import AsyncIOClient
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.dependencies.db import get_db
from app.dependencies.tg import get_tg

from ..schemas.auth import FullUser, Status
from .db_queries.select_current_user_async_edgeql import select_current_user

ALGORITHM = "HS256"


if TYPE_CHECKING:
    from telethon.types import User as TgUser


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class NotAuthenticatedError(Exception):
    pass


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db_client: AsyncIOClient, username: str) -> FullUser | None:
    user = await db_client.query(
        """select User {
                username,
                is_teacher,
                is_student,
                is_admin,
            }
            filter User.username = <str>$username
            limit 1
            """,
        username=username,
    )
    if user:
        return user[0]
    return None


async def get_user_by_id(db_client: AsyncIOClient, user_id: UUID):
    user = await db_client.query_single_json(
        """select User {first_name, last_name, status, id, email, username, is_teacher, is_student, is_admin, tg_id}
            filter User.id = <uuid>$id
            limit 1
            """,
        id=user_id,
    )
    return orjson.loads(user)


async def get_users(db_client: AsyncIOClient = Depends(get_db)):
    users = await db_client.query_json(
        """select User {first_name, last_name, status, id, email, username, tg_id}
            """,
    )
    return orjson.loads(users)


async def get_tg_name_by_tg_id(tg_id, tg_client):
    if tg_id is not None:
        tg_user: TgUser = await tg_client.get_entity(tg_id)
        return tg_user.username or tg_user.phone
    return None


async def get_users_with_tg_name(
    users=Depends(get_users), tg_client=Depends(get_tg)
):
    for user in users:
        user["tg_name"] = await get_tg_name_by_tg_id(user["tg_id"], tg_client)
    return users


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.secret_key.get_secret_value(), algorithm=ALGORITHM
    )


async def get_current_user(
    db_client: AsyncIOClient = Depends(get_db),
) -> FullUser | None:
    user = await select_current_user(db_client)
    if user is None:
        return None

    return FullUser(
        first_name=user.first_name,
        last_name=user.last_name,
        status=Status(user.status),
        id=user.id,
        is_teacher=user.is_teacher,
        is_student=user.is_student,
        is_admin=user.is_admin,
        is_parent=user.is_parent,
    )


async def get_current_active_user(
    current_user: FullUser | None = Depends(get_current_user),
) -> FullUser | None:
    # TODO: do smth with exceptions, middleware?
    return current_user
    if current_user.status != Status.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def allow_access(teacher=False, student=False):
    async def inner(user=Depends(get_current_active_user)):
        if user.is_admin is True:
            return user
        if user.is_teacher and teacher is True:
            return user
        if user.is_student and student is True:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return inner
