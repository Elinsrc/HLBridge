# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from loguru import logger

from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.utils import Socket
from hlbridge.database.servers import get_servers


@Client.on_message(filters.text)
async def send_to_hl(c: Client, m: Message):
    sock = Socket()
    servers = await get_servers(active_only=True)

    for server in servers:
        if m.message_thread_id != server.get("topic_id"):
            continue

        server_name = server["server_name"]
        server_port = server["port"]
        connectionless_args = server["connectionless_args"]

        msg = f"(telegram) {m.from_user.username}: {m.text}"
        query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8"))

        await sock.send_msg(server_port, query)
        logger.info(f"[{server_name}] Telegram: <<< {m.from_user.username}: {m.text} >>>")
