from datetime import timedelta

import orjson
from edgedb.asyncio_client import AsyncIOClient
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from telethon import TelegramClient
from telethon.types import User as TgUser

from app.dependencies.db import get_db
from app.dependencies.tg import get_tg
from app.server.router import TrailingSlashAPIRouter

from ....dependencies.auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user,
    get_users_with_tg_name,
)
from ....schemas.auth import (
    CreateUserPayload,
    FullUser,
    Status,
    Token,
    UsersList,
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = TrailingSlashAPIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db_client=Depends(get_db)
):
    user = await get_user(db_client, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": orjson.dumps(
                {
                    "user_id": str(user.id),
                    "is_teacher": user.is_teacher,
                    "is_student": user.is_student,
                    "is_admin": user.is_admin,
                }
            ).decode()
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=FullUser)
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def post_user(
    user: CreateUserPayload = Depends(),
    db_client: AsyncIOClient = Depends(get_db),
    tg_client: TelegramClient = Depends(get_tg),
) -> FullUser:
    tg_id = None
    if user.tg_name is not None:
        tg_entity = await tg_client.get_entity(user.tg_name)
        match tg_entity:
            case TgUser(id=id_):
                tg_id = id_
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"TG name is {type(tg_entity)}, not user",
                )
    try:
        (created_user,) = await db_client.query(
            """
            WITH
            new_user := (INSERT User {
                first_name := <str>$first_name,
                last_name := <str>$last_name,
                status := <str>$status,
                username := <str>$username,
                hashed_password := <str>$hashed_password,
                tg_id := <optional int64>$tg_id
                })
            SELECT new_user {
                id,
                first_name,
                last_name,
                username,
                status,
                is_teacher,
                is_student,
                is_admin,
                tg_id,

            };
            """,
            first_name=user.first_name,
            last_name=user.last_name,
            status=Status.active.value,
            username=user.username,
            hashed_password=get_password_hash(user.password),
            tg_id=tg_id,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Username '{user.username}' already exists,"},
        ) from e
    return FullUser(
        id=created_user.id,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        username=created_user.username,
        status=created_user.status,
        is_teacher=created_user.is_teacher,
        is_student=created_user.is_student,
        is_admin=created_user.is_admin,
        tg_name=user.tg_name,
    )


@router.get("/users/", response_model=UsersList)
async def get_all_users(users=Depends(get_users_with_tg_name)):
    return UsersList(data=users)
