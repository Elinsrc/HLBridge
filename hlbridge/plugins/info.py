# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from loguru import logger

from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from hlbridge.utils import HLServer, remove_color_tags, commands
from hlbridge.utils.decorators import owner_only
from hlbridge.utils.localization import Strings, use_chat_lang

from hlbridge.database.servers import get_servers


@Client.on_message(filters.command("id"))
@use_chat_lang
async def get_id(c: Client, m: Message, s: Strings):
    try:
        chat_id = m.chat.id
        username = m.from_user.username or m.from_user.first_name
        topic_id = m.message_thread_id

        msg = f"User: {username} ({m.from_user.id})\nChat: {m.chat.title} ({chat_id})\nTopic ID: {topic_id}"
        await m.reply_text(msg)
    except Exception as e:
        logger.error(e)
        await m.reply_text(e)


@Client.on_message(filters.command("status"))
@use_chat_lang
async def status(c: Client, m: Message, s: Strings):
    keyboard = []

    servers = await get_servers(active_only=True)
    if not servers:
        await m.reply_text(s("status_no_servers"))
        return

    for server in servers:
        button = InlineKeyboardButton(
            text=server['server_name'],
            callback_data=f"server_info|{server['port']}|{server['protocol']}"
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await m.reply_text(s("status_select_server"), reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^server_info"))
@use_chat_lang
async def server_info(c: Client, m: CallbackQuery, s: Strings):
    _, port, protocol = m.data.split("|")

    status = HLServer("0.0.0.0", int(port), int(protocol))
    server_info = '\n'.join(await status.get_server_info())
    player_list = '\n'.join(await status.get_players())

    msg = f"<code>{server_info}"
    if player_list:
        msg += s("status_player_list_header").format(player_list=player_list)
    msg += "</code>"

    await m.message.edit_text(remove_color_tags(msg))
    await m.answer()


commands.add_command("id", "general")
commands.add_command("status", "general")
