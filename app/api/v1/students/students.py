from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import allow_access, get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import FullUser, InlineUser
from app.server.router import TrailingSlashAPIRouter

from ....schemas.students import (
    CreateStudentPayload,
    Student,
    StudentsList,
    UpdateStudentPayload,
)

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: CreateStudentPayload, db_client=Depends(get_db)
) -> Student:
    try:
        created_student = await db_client.query_single_json(
            """
            WITH
            new_student := (INSERT Student {
                user := (select User filter .id = <uuid>$user_id),
                class := (select Class filter .id = <uuid>$class_id),
                })
            SELECT new_student {
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
                class: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year
                }

            };
            """,
            user_id=payload.user_id,
            class_id=payload.class_id,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    response = Student.model_validate_json(created_student)
    return response


@router.get("/")
async def get_students(
    db_client=Depends(get_db), _: InlineUser = Depends(get_current_active_user)
) -> StudentsList:
    studentes = await db_client.query_json(
        """
            select Student {
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
                class: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year
                }
            }
            """
    )
    response = StudentsList(data=orjson.loads(studentes))
    return response


@router.get("/{student_id}")
async def get_student_by_id(
    student_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Student:
    student = await db_client.query_single_json(
        """
            select Student {
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
                class: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year
                }
            }
            filter .id = <uuid>$student_id
            """,
        student_id=student_id,
    )
    response = Student(**orjson.loads(student))
    return response


@router.patch("/{student_id}")
async def update_student(
    payload: UpdateStudentPayload,
    student_id: UUID,
    db_client=Depends(get_db),
    _: FullUser = Depends(allow_access(teacher=True, student=True)),
) -> Student:
    student = await db_client.query_single_json(
        """
        with updated_student := (update Student filter .id = <uuid>$student_id
        set {class := (select Class filter .id = <uuid>$class_id)}),
        select updated_student {
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
                class: {
                    id,
                    updated_at,
                    created_at,
                    name,
                    year
                }

            }
        """,
        student_id=student_id,
        class_id=payload.class_id,
    )
    response = Student(**orjson.loads(student))
    return response
