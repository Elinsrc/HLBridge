# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from loguru import logger
from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.utils import Socket
from hlbridge.database.servers import get_servers
from hlbridge.database.user_names import get_user_name


@Client.on_message(filters.text)
async def send_to_hl(c: Client, m: Message):
    sock = Socket()

    servers = await get_servers(active_only=True)
    user_name = await get_user_name(m.from_user.id) or m.from_user.username

    for server in servers:
        if m.message_thread_id != server.get("topic_id"):
            continue

        server_name = server["server_name"]
        server_port = server["port"]
        connectionless_args = server["connectionless_args"]

        msg = f"(telegram) {user_name}: {m.text}"
        query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8"))

        await sock.send_msg(server_port, query)
        logger.info(f"[{server_name}] Telegram: <<< {user_name}: {m.text} >>>")
