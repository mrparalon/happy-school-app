import inspect
from enum import Enum
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel

BaseClass = TypeVar("BaseClass", bound=BaseModel)


def as_form(cls):
    new_params = [
        inspect.Parameter(
            field_name,
            inspect.Parameter.POSITIONAL_ONLY,
            default=model_field.default,
            annotation=Annotated[
                model_field.annotation, *model_field.metadata, Form()
            ],
        )
        for field_name, model_field in cls.model_fields.items()
    ]

    cls.__signature__ = cls.__signature__.replace(parameters=new_params)

    return cls


class Status(Enum):
    active = "active"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: UUID


class BaseUser(BaseModel):
    first_name: str
    last_name: str
    tg_name: str | None = None


@as_form
class CreateUserPayload(BaseUser):
    password: str


class InlineUser(BaseUser):
    id: UUID
    status: Status


class FullUser(InlineUser):
    is_teacher: bool | None
    is_student: bool | None
    is_admin: bool | None
    is_parent: bool | None


class UsersList(BaseModel):
    data: list[FullUser]


class UserInDB(FullUser):
    hashed_password: str
