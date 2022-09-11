from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.students import Student
from app.schemas.subjects import Subject
from app.schemas.teachers import Teacher


class CreateHomeworkPayload(BaseModel):
    assignment: str
    assigned_to: list[UUID]
    assigned_by: UUID
    subject_id: UUID
    deadline: datetime


class UpdateHomeworkPayload(BaseModel):
    done_by_student: bool | None = None
    assignment: str | None = None
    grade: int | None = None


class Homework(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    assignment: str
    assigned_to: Student
    assigned_by: Teacher
    subject: Subject
    deadline: datetime
    done_by_student: bool
    grade: int | None = None


class HomeworksList(BaseModel):
    data: list[Homework]
