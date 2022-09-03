import edgedb

client = edgedb.asyncio_client.create_async_client()


async def get_db() -> edgedb.asyncio_client.AsyncIOClient:
    return client
