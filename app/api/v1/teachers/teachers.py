from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import InlineUser
from app.server.router import TrailingSlashAPIRouter

from ....schemas.teachers import (
    CreateTeacherPayload,
    Teacher,
    TeachersList,
    UpdateTeacherPayload,
)

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_teacher(
    payload: CreateTeacherPayload,
    db_client=Depends(get_db),
) -> Teacher:
    try:
        created_teacher = await db_client.query_single_json(
            """
            WITH
            new_teacher := (INSERT Teacher {
                user := (select User filter .id = <uuid>$user_id),
                classes := (
                    select Class filter .id in array_unpack(<array<uuid>>$class_ids)
                    ),
                subjects := (
                    select Subject filter .id in array_unpack(<array<uuid>>$subject_ids)
                    )
                })
            SELECT new_teacher {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                subjects: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
                classes: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year,
                    },
            };
            """,
            class_ids=payload.class_ids,
            subject_ids=payload.subject_ids,
            user_id=payload.user_id,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    response = Teacher.model_validate_json(created_teacher)
    return response


@router.get("/")
async def get_teachers(
    db_client=Depends(get_db), _: InlineUser = Depends(get_current_active_user)
) -> TeachersList:
    teacheres = await db_client.query_json(
        """
            SELECT Teacher {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                subjects: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
                classes: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year,
                    },
            };
            """
    )
    response = TeachersList(data=orjson.loads(teacheres))
    return response


@router.get("/{teacher_id}")
async def get_teacher_by_id(
    teacher_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Teacher:
    teacher = await db_client.query_single_json(
        """
            SELECT Teacher {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                subjects: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
                classes: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year,
                    },
            }
            filter .id = <uuid>$teacher_id
            """,
        teacher_id=teacher_id,
    )
    response = Teacher(**orjson.loads(teacher))
    return response


@router.patch("/{teacher_id}")
async def update_teacher_by_id(
    payload: UpdateTeacherPayload,
    teacher_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Teacher:
    if payload.class_ids is not None or payload.subject_ids is not None:
        query = """
        update Teacher { }
            filter .id = <uuid>$teacher_id
            set {
        """
        if payload.class_ids is not None:
            query += """
                classes := (
                    select Class filter .id in array_unpack(<array<uuid>>$class_ids)
                    ),
            """
        if payload.subject_ids is not None:
            query += """
                subjects := (
                    select Subject filter .id in array_unpack(<array<uuid>>$subject_ids)
                    ),
            """
        query += "}"
        query_args = payload.model_dump(exclude_none=True)
        await db_client.query_single_json(
            query, teacher_id=teacher_id, **query_args
        )

    teacher = await db_client.query_single_json(
        """
            SELECT Teacher {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                },
                subjects: {
                    id,
                    updated_at,
                    created_at,
                    name,
                },
                classes: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year,
                    },
            }
            filter .id = <uuid>$teacher_id
    """,
        teacher_id=teacher_id,
    )
    response = Teacher(**orjson.loads(teacher))
    return response
