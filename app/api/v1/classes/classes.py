from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import allow_access, get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import FullUser, InlineUser
from app.server.router import TrailingSlashAPIRouter

from ....schemas.classes import Class, ClassesList, CreateClassPayload

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: CreateClassPayload,
    db_client=Depends(get_db),
    _: FullUser = Depends(allow_access(teacher=True)),
) -> Class:
    try:
        created_class = await db_client.query_single_json(
            """
            WITH
            new_class := (INSERT Class {
                name := <str>$name,
                year := <int16>$year,
                })
            SELECT new_class {
                id,
                updated_at,
                created_at,
                name,
                year

            };
            """,
            name=payload.name,
            year=payload.year,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    return Class.model_validate_json(created_class)


@router.get("/")
async def get_classes(
    db_client=Depends(get_db), _: InlineUser = Depends(get_current_active_user)
) -> ClassesList:
    classes = await db_client.query_json(
        """
            select Class {
                id,
                updated_at,
                created_at,
                name,
                year
                }
            """
    )
    return ClassesList(data=orjson.loads(classes))


@router.get("/{class_id}")
async def get_class_by_id(
    class_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Class:
    class_ = await db_client.query_single_json(
        """
            select Class {
                id,
                updated_at,
                created_at,
                name,
                year
                }
            filter .id = <uuid>$class_id
            """,
        class_id=class_id,
    )
    return Class(**orjson.loads(class_))
