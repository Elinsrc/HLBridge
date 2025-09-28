# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

import re

from loguru import logger

from hydrogram import Client, filters
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified

from hlbridge.database.settings import (
    get_settings,
    set_settings
)

from hlbridge.database.admins import (
    add_to_admin,
    remove_from_admin,
    user_admin
)

from hlbridge.database.servers import (
    add_server,
    update_server,
    remove_server,
    toggle_server,
    get_server,
    get_servers
)

from hlbridge.utils import commands
from hlbridge.utils.decorators import owner_only
from hlbridge.utils.localization import Strings, use_chat_lang


@Client.on_message(filters.command("setup"))
@use_chat_lang
async def setup_bot(c: Client, m: Message, s: Strings):
    if m.chat.type == ChatType.PRIVATE:
        await m.reply(s("setup_private_chat"))
        return

    if m.message_thread_id is None:
        await m.reply(s("setup_no_topic"))
        return

    settings = await get_settings()

    if settings and settings["owner_id"] and settings["owner_id"] != m.from_user.id:
        await m.reply(s("setup_not_owner"))
        return

    try:
        await set_settings(m.from_user.id, m.chat.id, m.message_thread_id)
        await m.reply(
            s("setup_success").format(
                chat_id=m.chat.id,
                topic_id=m.message_thread_id,
                owner_id=m.from_user.id,
            )
        )
    except Exception as e:
        await m.reply(s("setup_error").format(error=str(e)))


@Client.on_message(filters.command("add_admin"))
@owner_only
@use_chat_lang
async def add_admin(c: Client, m: Message, s: Strings):
    if len(m.command) < 2:
        await m.reply(s("give_me_user_id"))
        return

    user_id = m.command[1]

    admin = await user_admin(user_id)
    if admin:
        await m.reply(s("already_added_admin"))
        return

    try:
        user = await c.get_users(user_id)
        username = user.username if user.username else "noname"

        await add_to_admin(user_id)
        await m.reply(s("user_added_to_admin").format(name=username, id=user_id))
    except Exception as e:
        await m.reply(f"Error: {str(e)}")


@Client.on_message(filters.command("del_admin"))
@owner_only
@use_chat_lang
async def del_admin(c: Client, m: Message, s: Strings):
    if len(m.command) < 2:
        await m.reply(s("give_me_user_id"))
        return

    user_id = m.command[1]

    try:
        admin = await user_admin(user_id)

        if admin:
            user = await c.get_users(user_id)
            username = user.username if user.username else "noname"

            await remove_from_admin(user_id)
            await m.reply(s("user_removed_from_admin").format(name=username, id=user_id))
        else:
            await m.reply(s("admin_not_found").format(id=user_id))
    except Exception as e:
        await m.reply(f"Error: {str(e)}")


def build_servers_keyboard(servers_list):
    keyboard = []
    for server in servers_list:
        status_icon = "🟢" if server["is_active"] else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {server['server_name']}",
                callback_data=f"manage_server|{server['server_name']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔄", callback_data="back_to_servers")])
    return InlineKeyboardMarkup(keyboard)


async def safe_edit_message(query: CallbackQuery, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        pass


@Client.on_message(filters.command("servers"))
@owner_only
@use_chat_lang
async def list_servers(c: Client, m: Message, s: Strings):
    if m.chat.type != ChatType.PRIVATE:
        await m.reply(s("only_private_chat"))
        return

    servers_list = await get_servers()
    if not servers_list:
        await m.reply(s("no_servers"))
        return

    keyboard = build_servers_keyboard(servers_list)
    await m.reply(s("server_list_header"), reply_markup=keyboard)


@Client.on_message(filters.command("add_server"))
@owner_only
@use_chat_lang
async def add_server_command(c: Client, m: Message, s: Strings):
    if m.chat.type != ChatType.PRIVATE:
        await m.reply(s("only_private_chat"))
        return

    try:
        args = re.findall(r"\[([^\]]+)\]", m.text)

        if len(args) != 7:
            await m.reply(s("add_server_usage"))
            return

        try:
            port = int(args[1].strip())
            log_port = int(args[2].strip())
            oldengine = int(args[3].strip())
            topic_id = int(args[4].strip())
        except ValueError:
            await m.reply(s("value_error"))
            return

        servers_list = await get_servers()
        for srv in servers_list:
            if srv["topic_id"] == topic_id:
                await m.reply(s("topic_id_already_used").format(topic_id=topic_id))
                return

        server = {
            "server_name": args[0].strip(),
            "port": port,
            "log_port": log_port,
            "oldengine": oldengine,
            "topic_id": topic_id,
            "connectionless_args": args[5].strip(),
            "rcon_password": args[6].strip(),
        }

        if not (1 <= port <= 65535):
            await m.reply(s("invalid_port"))
            return
        if not (1 <= log_port <= 65535):
            await m.reply(s("invalid_log_port"))
            return
        if port == log_port:
            await m.reply(s("ports_cannot_be_same"))
            return

        await add_server(server)
        await m.reply(s("server_added").format(name=server["server_name"]))

    except Exception as e:
        await m.reply(e)


@Client.on_message(filters.command("update_server"))
@owner_only
@use_chat_lang
async def update_server_command(c: Client, m: Message, s: Strings):
    if m.chat.type != ChatType.PRIVATE:
        await m.reply(s("only_private_chat"))
        return

    try:
        args = re.findall(r"\[([^\]]+)\]", m.text)

        if len(args) < 2:
            await m.reply(s("update_server_usage"))
            return

        server_name = args[0].strip()
        existing = await get_server(server_name)
        if not existing:
            await m.reply(s("server_not_found").format(name=server_name))
            return

        updates = {}

        for arg in args[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key in ["port", "log_port", "oldengine", "topic_id"]:
                    try:
                        value = int(value)
                    except ValueError:
                        await m.reply(s("value_error"))
                        return

                updates[key] = value

        if "topic_id" in updates:
            servers_list = await get_servers()
            for srv in servers_list:
                if srv["topic_id"] == updates["topic_id"] and srv["server_name"] != server_name:
                    await m.reply(s("topic_id_already_used").format(topic_id=updates["topic_id"]))
                    return

        if "port" in updates and not (1 <= updates["port"] <= 65535):
            await m.reply(s("invalid_port"))
            return
        if "log_port" in updates and not (1 <= updates["log_port"] <= 65535):
            await m.reply(s("invalid_log_port"))
            return
        if "port" in updates and "log_port" in updates and updates["port"] == updates["log_port"]:
            await m.reply(s("ports_cannot_be_same"))
            return

        await update_server(server_name, updates)
        await m.reply(s("server_updated").format(name=server_name))

    except Exception as e:
        await m.reply(f"{s('server_error')}: {str(e)}")


@Client.on_callback_query(filters.regex("^manage_server"))
@owner_only
@use_chat_lang
async def manage_server(c: Client, q: CallbackQuery, s: Strings):
    _, server_name = q.data.split("|", 1)
    server = await get_server(server_name)

    if not server:
        await q.answer(s("server_not_found").format(name=server_name), show_alert=True)
        return

    status_text = s("active") if server["is_active"] else s("inactive")

    msg = (
        f"{server['server_name']}\n"
        f"{status_text}\n"
        f"port: {server['port']}\n"
        f"log_port: {server['log_port']}\n"
        f"oldengine: {server['oldengine']}\n"
        f"topic_id: {server['topic_id']}\n"
        f"connectionless_args: {server['connectionless_args']}\n"
        f"rcon_password: {server['rcon_password']}\n"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄", callback_data=f"toggle_server_cb|{server_name}"),
            InlineKeyboardButton("❌", callback_data=f"remove_server_cb|{server_name}")
        ],
        [
            InlineKeyboardButton(s("general_back_btn"), callback_data="back_to_servers")
        ]
    ])

    await safe_edit_message(q, msg, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^toggle_server_cb"))
@owner_only
@use_chat_lang
async def toggle_server_cb(c: Client, q: CallbackQuery, s: Strings):
    _, server_name = q.data.split("|", 1)
    status = await toggle_server(server_name)
    await manage_server(c, q, s)


@Client.on_callback_query(filters.regex("^remove_server_cb"))
@owner_only
@use_chat_lang
async def confirm_remove_server(c: Client, q: CallbackQuery, s: Strings):
    _, server_name = q.data.split("|", 1)
    server = await get_server(server_name)
    if not server:
        await q.answer(s("server_not_found").format(name=server_name), show_alert=True)
        return
    msg = s("confirm_remove_server").format(name=server_name)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(s("yes_btn"), callback_data=f"confirm_remove_yes|{server_name}"),
            InlineKeyboardButton(s("no_btn"), callback_data=f"confirm_remove_no|{server_name}")
        ]
    ])
    await safe_edit_message(q, msg, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^confirm_remove_yes"))
@owner_only
@use_chat_lang
async def remove_server_yes(c: Client, q: CallbackQuery, s: Strings):
    _, server_name = q.data.split("|", 1)
    server = await get_server(server_name)
    if server:
        await remove_server(server_name)
        await q.answer(s("server_deleted").format(name=server_name), show_alert=True)
    else:
        await q.answer(s("server_not_found").format(name=server_name), show_alert=True)
    await q.message.delete()


@Client.on_callback_query(filters.regex("^confirm_remove_no"))
@owner_only
@use_chat_lang
async def remove_server_no(c: Client, q: CallbackQuery, s: Strings):
    server_name = q.data.split("|")[1]
    await q.answer(s("remove_cancelled"), show_alert=True)
    await q.message.delete()


@Client.on_callback_query(filters.regex("^back_to_servers"))
@owner_only
@use_chat_lang
async def back_to_servers(c: Client, q: CallbackQuery, s: Strings):
    servers_list = await get_servers()
    if not servers_list:
        await safe_edit_message(q, s("no_servers"))
        return

    keyboard = build_servers_keyboard(servers_list)
    await safe_edit_message(q, s("server_list_header"), reply_markup=keyboard)


commands.add_command("setup", "owner")
commands.add_command("add_admin", "owner")
commands.add_command("del_admin", "owner")
commands.add_command("servers", "owner")
commands.add_command("add_server", "owner")
commands.add_command("update_server", "owner")
