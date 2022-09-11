from uuid import UUID

import orjson
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, Response, status

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.schemas.auth import InlineUser
from app.schemas.students import StudentsList
from app.server.router import TrailingSlashAPIRouter

from ....schemas.parents import CreateParentPayload, Parent, ParentsList

router = TrailingSlashAPIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_parent(
    payload: CreateParentPayload,
    db_client=Depends(get_db),
) -> Parent:
    try:
        created_parent = await db_client.query_single_json(
            """
            WITH
            new_parent := (INSERT Parent {
                user := (select User filter .id = <uuid>$user_id),
                })
            SELECT new_parent {
                id,
                updated_at,
                created_at,
                user: {
                    id,
                    first_name,
                    last_name,
                    username,
                    status
                }

            };
            """,
            user_id=payload.user_id,
        )
    except ConstraintViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from e
    return Parent.model_validate_json(created_parent)


@router.get("/")
async def get_parents(
    db_client=Depends(get_db), _: InlineUser = Depends(get_current_active_user)
) -> ParentsList:
    parentes = await db_client.query_json(
        """
            select Parent {
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
            }
            """
    )
    return ParentsList(data=orjson.loads(parentes))


@router.get("/{parent_id}")
async def get_parent_by_id(
    parent_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> Parent:
    parent = await db_client.query_single_json(
        """
            select Parent {
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
            }
            filter .id = <uuid>$parent_id
            """,
        parent_id=parent_id,
    )
    response = Parent(**orjson.loads(parent))
    return response


@router.post("/{parent_id}/children/{children_id}")
async def add_parent_child(
    parent_id: UUID,
    children_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
):
    await db_client.query_single_json(
        """
        update Parent
        filter .id = <uuid>$parent_id
        set {
            children += (
                select Student {}
                filter .id = <uuid>$children_id
                )
            }
            """,
        parent_id=parent_id,
        children_id=children_id,
    )
    return


@router.delete("/{parent_id}/children/{children_id}")
async def delete_parent_child(
    parent_id: UUID,
    children_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
):
    await db_client.query_single_json(
        """
        update Parent
        filter .id = <uuid>$parent_id
        set {
            children -= (
                select Student
                filter .id = <uuid>$children_id
                )
            }
            """,
        parent_id=parent_id,
        children_id=children_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{parent_id}/children")
async def get_parent_children(
    parent_id: UUID,
    db_client=Depends(get_db),
    _: InlineUser = Depends(get_current_active_user),
) -> StudentsList:
    students = await db_client.query_json(
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
            filter .parents.id = <uuid>$parent_id
            """,
        parent_id=parent_id,
    )
    response = StudentsList(data=orjson.loads(students))
    return response
