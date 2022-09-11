import io

import orjson
import qrcode
from happy_school_bot.db_queries.create_qr_code_async_edgeql import (
    create_qr_code,
)
from happy_school_bot.db_queries.find_active_qr_code_by_parent_user_id_async_edgeql import (
    find_active_qr_code_by_parent_user_id,
)
from happy_school_bot.db_queries.get_children_by_parent_user_id_async_edgeql import (
    get_children_by_parent_user_id,
)
from happy_school_bot.db_queries.get_user_by_tg_id_async_edgeql import (
    GetUserByTgIdResult,
)
from telethon import Button


async def parent_handler(db_client, event, user: GetUserByTgIdResult):
    children = await get_children_by_parent_user_id(db_client, parent_user_id=user.id)
    if not children:
        await event.message.respond("You don't have kids registered. Please contact to administrator")
        return

    if len(children) > 1:
        await event.message.respond("For now we only support One child")
        return

    qr_codes = await find_active_qr_code_by_parent_user_id(
        db_client,
        parent_user_id=user.id,
    )
    if not qr_codes:
        qr_code = await create_qr_code(
            db_client,
            student_ids=[i.id for i in children],
            parent_user_id=user.id,
        )
    else:
        qr_code = qr_codes[0]
    img = qrcode.make(f"https://t.me/happy_school_bot?start={qr_code.id}")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="png")

    markup = event.client.build_reply_markup(
        [
            Button.inline(
                "Новый qr",
                data=orjson.dumps(["/new_qr", {"old_qr_id": str(qr_code.id)}]),
            ),
        ]
    )

    await event.respond(
        f"Мы нашли у вас одного ребенка: {children[0].user.first_name}."
        "\nЧтобы отдать его в школу или забрать из школы, покажите QR код администратору на входе.",
        file=img_byte_arr.getvalue(),
        buttons=markup,
    )
