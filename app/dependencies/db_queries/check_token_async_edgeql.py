# AUTOGENERATED FROM 'app/dependencies/db_queries/check_token.edgeql' WITH:
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
class CheckTokenResult(NoPydanticValidation):
    id: uuid.UUID


async def check_token(
    executor: edgedb.AsyncIOExecutor,
) -> CheckTokenResult | None:
    return await executor.query_single(
        """\
        select global ext::auth::ClientTokenIdentity\
        """,
    )
