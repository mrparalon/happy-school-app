from fastapi import Depends, HTTPException, status, APIRouter
from uuid import UUID

from .schemas import CreateClassPayload, Class, ClassesList
from app.api.v1.dependencies.db import get_db
from app.api.v1.auth.dependencies import get_current_active_user
from app.api.v1.auth.schemas import User
from edgedb.errors import ConstraintViolationError
import orjson

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_class(payload: CreateClassPayload, db_client=Depends(get_db)) -> Class:
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
    except ConstraintViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = Class.parse_raw(created_class)
    return response


@router.get("/")
async def get_classes(db_client=Depends(get_db), _: User = Depends(get_current_active_user)) -> ClassesList:
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
    response = ClassesList(data=orjson.loads(classes))
    return response


@router.get("/{class_id}")
async def get_class_by_id(
    class_id: UUID, db_client=Depends(get_db), _: User = Depends(get_current_active_user)
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
    response = Class(**orjson.loads(class_))
    return response
