from telethon import TelegramClient

from app.config import settings

client = TelegramClient("@mrparalon", settings.API_ID, settings.API_HASH)


async def get_tg() -> TelegramClient:
    return client
