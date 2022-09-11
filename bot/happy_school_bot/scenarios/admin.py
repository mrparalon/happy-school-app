from uuid import UUID

import orjson
from edgedb import AsyncIOClient
from happy_school_bot.db_queries.get_qr_code_by_id_async_edgeql import (
    get_qr_code_by_id,
)
from happy_school_bot.db_queries.get_user_by_tg_id_async_edgeql import (
    GetUserByTgIdResult,
)
from telethon import Button


async def admin_handler(
    db_client: AsyncIOClient,
    event,
    user: GetUserByTgIdResult,  # noqa: ARG001
):
    words = event.message.text.split(" ")
    if words[0] != "/start":
        await event.respond("Wrong command")
        return
    if len(words) == 1:
        await event.respond(
            "Сосканируйте QR код. Можно использовать приложение google lens, "
            "камеру Айфона или любое приложение для сканирования QR кодов"
        )
    try:
        qr_code_id = UUID(words[1])
    except (ValueError, IndexError):
        await event.respond("Похоже, QR код неправильный. Попросите родителя сгенерировать новый")
        return
    qr_code_data = await get_qr_code_by_id(db_client, qr_code_id=qr_code_id)
    if qr_code_data is None:
        await event.respond("Похоже, QR код неправильный. Попросите родителя сгенерировать новый")
        return
    student_names_formated = ", ".join([f"{i.user.first_name} {i.user.last_name}" for i in qr_code_data.students])
    markup = event.client.build_reply_markup(
        [
            Button.inline(
                "Привели",
                data=orjson.dumps(["/qr_in", {"qr_id": str(qr_code_id)}]),
            ),
            Button.inline(
                "Забрали",
                data=orjson.dumps(["/qr_out", {"qr_id": str(qr_code_id)}]),
            ),
        ]
    )
    await event.respond(
        f"Дети: {student_names_formated}\n"
        f"Родитель {qr_code_data.parent.user.first_name} {qr_code_data.parent.user.last_name}",
        buttons=markup,
    )
