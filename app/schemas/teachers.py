from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import Field

from app.schemas.auth import InlineUser
from app.schemas.classes import Class
from app.schemas.subjects import Subject


class CreateTeacherPayload(BaseModel):
    user_id: UUID
    class_ids: list[UUID]
    subject_ids: list[UUID]


class UpdateTeacherPayload(BaseModel):
    class_ids: list[UUID] | None = None
    subject_ids: list[UUID] | None = None


class Teacher(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    user: InlineUser
    classes: list[Class] = Field(default_factory=list)
    subjects: list[Subject] = Field(default_factory=list)


class TeachersList(BaseModel):
    data: list[Teacher]
