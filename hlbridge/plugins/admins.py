import re
import io

from hydrogram import Client, filters
from hydrogram.types import Message
from hydrogram.enums import ChatType

from hlbridge.database.user_names import set_user_name, get_user_name, remove_user_name, get_all_user_names
from hlbridge.database.admins import user_admin
from hlbridge.database.settings import user_owner

from hlbridge.utils import HLServer, remove_color_tags, commands
from hlbridge.utils.decorators import admin_only
from hlbridge.utils.localization import Strings, use_chat_lang
from hlbridge.database.servers import get_servers


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


@Client.on_message(filters.command("rcon"))
@admin_only
@use_chat_lang
async def rcon_command(c: Client, m: Message, s: Strings):
    if m.chat.type == ChatType.PRIVATE:
        await m.reply(s("rcon_private_chat"))
        return

    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        await m.reply(s("rcon_usage"))
        return

    command_text = args[1].strip()

    servers = await get_servers()
    server = next(
        (srv for srv in servers if srv["topic_id"] == m.message_thread_id and srv["is_active"]),
        None
    )

    if not server:
        await m.reply(f"{s('rcon_not_allowed')}")
        return

    protocol = 48 if server['oldengine'] == 1 else 49
    hlserver = HLServer(ip="0.0.0.0", port=server["port"], protocol=protocol, timeout=0.5)

    result = await hlserver.rcon(server["rcon_password"], command_text)
    result = remove_color_tags(result)

    if not result.strip():
        await m.reply(s("rcon_no_response"))
        return

    if len(result) < 3500:
        await m.reply(f"<code>{result}</code>")
        return

    bio = io.BytesIO(result.encode('utf-8'))
    bio.name = "rcon_result.txt"

    await m.reply_document(bio)


commands.add_command("set_name", "admins")
commands.add_command("remove_name", "admins")
commands.add_command("custom_names", "general")
commands.add_command("rcon", "admins")
