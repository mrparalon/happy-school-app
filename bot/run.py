from datetime import datetime
from enum import Enum
from typing import AsyncIterator
from uuid import UUID
import os

import edgedb
import orjson
from happy_school_bot.db_queries.check_child_async_edgeql import check_child
from happy_school_bot.db_queries.get_qr_code_by_id_async_edgeql import (
    GetQrCodeByIdResult,
    get_qr_code_by_id,
)
from happy_school_bot.db_queries.get_user_by_tg_id_async_edgeql import (
    get_user_by_tg_id,
)
from happy_school_bot.scenarios.admin import admin_handler
from happy_school_bot.scenarios.parent import parent_handler
from telethon import Button, TelegramClient, events

db_client = edgedb.asyncio_client.create_async_client()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

client = TelegramClient("anon", API_ID, API_HASH)


class CheckoutActions(Enum):
    exit = "exit"
    entrance = "entrance"


async def get_parents_to_notify(
    tg_client, qr_code_object: GetQrCodeByIdResult
) -> AsyncIterator[int]:
    parents_to_notify = set()
    for student in qr_code_object.students:
        for parent in student.parents:
            parents_to_notify.add(parent.user.tg_id)
    for parent in parents_to_notify:
        yield await tg_client.get_entity(parent.user.tg_id)


async def notify_parents(tg_client, action: CheckoutActions, qr_id: UUID):
    qr_code_object = await get_qr_code_by_id(db_client, qr_code_id=qr_id)
    if qr_code_object is None:
        # TODO: add error message
        # https://example.com
        return
    match action:
        case CheckoutActions.exit:
            message = "Ваш ребенок {} ушел из школы."
        case CheckoutActions.entrance:
            message = "Ваш ребенок {} пришел в школу."
        case _:
            # TODO: add error
            # https://example.com
            return
    async for parent in get_parents_to_notify(
        tg_client.client, qr_code_object
    ):
        await tg_client.send_message(
            parent, message.format(qr_code_object.students[0].user.first_name)
        )


@client.on(events.NewMessage())
async def my_event_handler(event):
    if not event.chat_id:
        return None
    user = await client.get_entity(event.chat_id)
    user = await get_user_by_tg_id(db_client, tg_id=event.chat_id)
    if user is None:
        await event.respond("I don't know you")
        return None
    await event.respond(f"Добрый день, {user.first_name} {user.last_name}")
    if user.is_parent:
        return await parent_handler(db_client, event, user)
    if user.is_admin:
        return await admin_handler(db_client, event, user)
    return None


@client.on(events.CallbackQuery())
async def inline_handler(event):
    if not event.chat_id:
        return
    user = await get_user_by_tg_id(db_client, tg_id=event.chat_id)
    if user is None:
        await event.respond("I don't know you")
        return
    message = await event.get_message()
    if user.is_admin:
        match orjson.loads(event.data):
            case ["/qr_in", {"qr_id": qr_id}]:
                await check_child(
                    db_client,
                    qrcode_id=qr_id,
                    action=CheckoutActions.entrance.value,
                    checked_by=user.id,
                )
                markup = event.client.build_reply_markup(
                    [
                        Button.inline(
                            "➡️Пришел",
                            data=orjson.dumps(["/no_action", {}]),
                        ),
                    ]
                )
                await event.edit(
                    f"{message.text}\nПривели {datetime.now().strftime('%d-%m-%Y %X')}",
                    buttons=markup,
                )
            case ["/qr_out", {"qr_id": qr_id}]:
                await check_child(
                    db_client,
                    qrcode_id=qr_id,
                    action=CheckoutActions.exit.value,
                    checked_by=user.id,
                )
                markup = event.client.build_reply_markup(
                    [
                        Button.inline(
                            "⬅️Ушел",
                            data=orjson.dumps(["/no_action", {}]),
                        ),
                    ]
                )
                await event.edit(
                    f"{message.text}\nЗабрали {datetime.now().strftime('%d-%m-%Y %X')}",
                    buttons=markup,
                )
            case ["/no_action", *_]:
                return
            case _:
                return


client.start()
client.run_until_disconnected()
