from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import allow_access, get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import FullUser, InlineUser
from app.server.router import TrailingSlashAPIRouter

from ....schemas.subjects import CreateSubjectPayload, Subject, SubjectsList

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: CreateSubjectPayload,
    db_client=Depends(get_db),
    _: FullUser = Depends(allow_access(teacher=True)),
) -> Subject:
    try:
        created_subject = await db_client.query_single_json(
            """
            WITH
            new_subject := (INSERT Subject {
                name := <str>$name
                })
            SELECT new_subject {
                id,
                updated_at,
                created_at,
                name,
            };
            """,
            name=payload.name,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    response = Subject.model_validate_json(created_subject)
    return response


@router.get("/")
async def get_subjects(
    db_client=Depends(get_db), _: InlineUser = Depends(get_current_active_user)
) -> SubjectsList:
    subjectes = await db_client.query_json(
        """
            select Subject {
                id,
                updated_at,
                created_at,
                name,
            }
            """
    )
    response = SubjectsList(data=orjson.loads(subjectes))
    return response


@router.get("/{subject_id}")
async def get_subject_by_id(
    subject_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Subject:
    subject = await db_client.query_single_json(
        """
            select Subject {
                id,
                updated_at,
                created_at,
                name,
            }
            filter .id = <uuid>$subject_id
            """,
        subject_id=subject_id,
    )
    response = Subject(**orjson.loads(subject))
    return response
