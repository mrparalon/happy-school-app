from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateClassPayload(BaseModel):
    name: str
    year: int


class Class(CreateClassPayload):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ClassesList(BaseModel):
    data: list[Class]
