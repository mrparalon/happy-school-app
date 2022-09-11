import edgedb
from fastapi import Cookie

client = edgedb.asyncio_client.create_async_client().with_module_aliases(
    {"auth": "ext::auth"}
)


async def get_db(
    edgedb_auth_token: str
    | None = Cookie(
        None,
    )
) -> edgedb.asyncio_client.AsyncIOClient:
    if edgedb_auth_token is not None:
        return client.with_globals(
            {
                "auth::client_token": edgedb_auth_token,
            }
        )
    return client
