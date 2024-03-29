# AUTOGENERATED FROM 'bot/happy_school_bot/db_queries/create_qr_code.edgeql' WITH:
#     $ edgedb-py


from __future__ import annotations
import dataclasses
import edgedb
import uuid


class NoPydanticValidation:
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        # Pydantic 2.x
        from pydantic_core.core_schema import any_schema
        return any_schema()

    @classmethod
    def __get_validators__(cls):
        # Pydantic 1.x
        from pydantic.dataclasses import dataclass as pydantic_dataclass
        pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


@dataclasses.dataclass
class CreateQrCodeResult(NoPydanticValidation):
    id: uuid.UUID


async def create_qr_code(
    executor: edgedb.AsyncIOExecutor,
    *,
    student_ids: list[uuid.UUID],
    parent_user_id: uuid.UUID,
) -> CreateQrCodeResult:
    return await executor.query_single(
        """\
        insert EntranceQRcode {
            students := (
                select Student filter .id in array_unpack(<array<uuid>>$student_ids)
            ),
            parent := (
                select Parent filter .user.id = <uuid>$parent_user_id
            )
        }\
        """,
        student_ids=student_ids,
        parent_user_id=parent_user_id,
    )
