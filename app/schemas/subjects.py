from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateSubjectPayload(BaseModel):
    name: str


class Subject(CreateSubjectPayload):
    id: UUID
    created_at: datetime
    updated_at: datetime


class SubjectsList(BaseModel):
    data: list[Subject]
