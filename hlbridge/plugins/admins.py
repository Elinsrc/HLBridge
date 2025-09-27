import re

from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.database.user_names import set_user_name, get_user_name, remove_user_name, get_all_user_names
from hlbridge.database.admins import user_admin
from hlbridge.database.settings import user_owner

from hlbridge.utils import commands
from hlbridge.utils.decorators import admin_only
from hlbridge.utils.localization import Strings, use_chat_lang


async def protected_user(user_id: int) -> bool:
    return await user_owner(user_id) or await user_admin(user_id)


@Client.on_message(filters.command("set_name"))
@admin_only
@use_chat_lang
async def set_name_command(c: Client, m: Message, s: Strings):
    import re
    args = re.findall(r"\[([^\]]+)\]", m.text)

    if len(args) == 1:
        target_user_id = m.from_user.id
        user_name = args[0].strip()
        default_name = m.from_user.username
    elif len(args) == 2:
        try:
            target_user_id = int(args[0].strip())
        except ValueError:
            await m.reply(s("invalid_user_id"))
            return

        user_name = args[1].strip()
        user = await c.get_users(target_user_id)
        default_name = user.first_name
    else:
        await m.reply(s("set_name_usage"))
        return

    if await protected_user(target_user_id) and target_user_id != m.from_user.id:
        await m.reply(s("cannot_change_admin_or_owner"))
        return

    await set_user_name(target_user_id, default_name=default_name, custom_name=user_name)
    await m.reply(s("set_name_success").format(name=user_name))



@Client.on_message(filters.command("remove_name"))
@admin_only
@use_chat_lang
async def remove_name_command(c: Client, m: Message, s: Strings):
    args = re.findall(r"\[([^\]]+)\]", m.text)

    if len(args) != 1:
        await m.reply(s("remove_name_usage"))
        return

    arg = args[0].strip().lower()
    if arg == "me":
        target_user_id = m.from_user.id
    else:
        try:
            target_user_id = int(arg)
        except ValueError:
            await m.reply(s("invalid_user_id"))
            return

    if await protected_user(target_user_id) and target_user_id != m.from_user.id:
        await m.reply(s("cannot_change_admin_or_owner"))
        return

    existing_name = await get_user_name(target_user_id)
    if not existing_name:
        await m.reply(s("no_custom_name"))
        return

    await remove_user_name(target_user_id)
    await m.reply(s("remove_name_success"))


@Client.on_message(filters.command("custom_names"))
@use_chat_lang
async def my_name_command(c: Client, m: Message, s: Strings):
    users = await get_all_user_names()

    users_custom_name = [
        (user_id, default_name, custom_name)
        for user_id, default_name, custom_name in users
        if custom_name
    ]

    if not users_custom_name:
        await m.reply(s("no_custom_name"))
        return

    msg_lines = []
    for user_id, default_name, custom_name in users_custom_name:
        line = f"{default_name} (ID: {user_id}) — {custom_name}"
        msg_lines.append(line)

    msg = "\n".join(msg_lines)

    await m.reply(msg)


commands.add_command("set_name", "admins")
commands.add_command("remove_name", "admins")
commands.add_command("custom_names", "general")
