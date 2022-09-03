from pydantic import BaseModel
from enum import Enum
from uuid import UUID
import inspect
from typing import Type, TypeVar, Generic

BaseClass = TypeVar("BaseClass", bound=BaseModel)

from fastapi import Form
from pydantic.fields import ModelField

def as_form(cls: BaseClass) -> BaseClass:
    new_parameters = []

    for _, model_field in cls.__fields__.items():
        model_field: ModelField  # type: ignore

        new_parameters.append(
             inspect.Parameter(
                 model_field.alias,
                 inspect.Parameter.POSITIONAL_ONLY,
                 default=Form(...) if model_field.required else Form(model_field.default),
                 annotation=model_field.outer_type_,
             )
         )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_form', as_form_func)
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
    username: str
    email: str | None = None


@as_form
class CreateUserPayload(BaseUser):
    password: str

class User(BaseUser):
    id: UUID
    status: Status

class UsersList(BaseModel):
    data: list[User]


class UserInDB(User):
    hashed_password: str
