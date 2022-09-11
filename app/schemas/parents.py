from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.auth import InlineUser


class CreateParentPayload(BaseModel):
    user_id: UUID


class Parent(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    user: InlineUser


class ParentsList(BaseModel):
    data: list[Parent]
