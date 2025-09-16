from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from hydrogram.enums import ParseMode

from hlbridge.utils import Utils, HLServer
from hlbridge.config import SERVERS

@Client.on_message(filters.command("id"))
async def get_id(c: Client, m: Message):
    try:
        msg = f"```Name ID\n{m.from_user.username}: {m.from_user.id}\n{m.chat.title}: {m.chat.id}```"
        await m.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await m.reply_text(e)

@Client.on_message(filters.command("status"))
async def status(c: Client, m: Message):
    keyboard = []

    for server in SERVERS:
        protocol = 48 if server['oldengine'] == 1 else 49

        button = InlineKeyboardButton(
            text=server['server_name'],
            callback_data=f"server_info|{server['ip']}|{server['port']}|{protocol}"
        )

        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await m.reply_text("Select server:", reply_markup=reply_markup)

@Client.on_callback_query(filters.regex("^server_info"))
async def server_info(c: Client, query: CallbackQuery):
    _, ip, port, protocol = query.data.split("|")

    status = HLServer(ip, int(port), int(protocol), 0.5)
    server_info = '\n'.join(await status.get_server_info())
    player_list = '\n'.join(await status.get_players())

    msg = f"```{server_info}"
    if player_list:
        msg += f"\n\n# Name [kills] (Time)\n{player_list}"
    msg += "```"

    await query.message.edit_text(Utils.remove_color_tags(msg), parse_mode=ParseMode.MARKDOWN)
    await query.answer()

@Client.on_message(filters.command(["start","help"]))
async def get_help(c: Client, m: Message):
    msg = "/id - shows the chat_id and user_id\n"
    msg += "/status - shows players and their statistics"
    await m.reply_text(msg)
