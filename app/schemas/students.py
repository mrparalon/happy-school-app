from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import Field

from app.schemas.auth import InlineUser
from app.schemas.classes import Class


class CreateStudentPayload(BaseModel):
    user_id: UUID
    class_id: UUID | None


class UpdateStudentPayload(BaseModel):
    class_id: UUID


class Student(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    user: InlineUser
    class_: Class = Field(alias="class")


class StudentsList(BaseModel):
    data: list[Student]
