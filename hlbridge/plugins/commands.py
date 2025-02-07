from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.utils import Utils, HLServer
from hlbridge.envars import (
    SERVER_IP,
    SERVER_PORT,
    CONNECTIONLESS_ARGS,
)

from __main__ import protocol

@Client.on_message(filters.command("id"))
async def get_id(c: Client, m: Message):
    try:
        msg = f"```Name ID\n{m.from_user.username}: {m.from_user.id}\n{m.chat.title}: {m.chat.id}```"
        await m.reply_text(msg)
    except Exception as e:
        await m.reply_text(e)

@Client.on_message(filters.command("status"))
async def status(c: Client, m: Message):
    status = HLServer(SERVER_IP, SERVER_PORT, protocol, 0.5)
    server_info = '\n'.join(await status.get_server_info())
    player_list = '\n'.join(await status.get_players())
    msg = f"{server_info}"
    if player_list:
        msg += f"\n\n# Name [kills] (Time)\n{player_list}"
    await m.reply_text(Utils.remove_color_tags(msg))
