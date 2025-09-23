from loguru import logger

from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.utils import Socket
from hlbridge.config import SERVERS, CHAT_ID


@Client.on_message(filters.text & ~filters.command(["start", "help", "status", "id"]))
async def send_to_hl(c: Client, m: Message):
    sock = Socket()
    for server in SERVERS:
        if m.message_thread_id != server["topic_id"]:
            continue

        server_name = server["server_name"]
        server_ip = server["ip"]
        server_port = server["port"]
        connectionless_args = server["connectionless_args"]

        msg = f"(telegram) {m.from_user.username}: {m.text}"
        query = b'\xff\xff\xff\xff%b %b\n' % (connectionless_args.encode(), msg.encode("utf8") )
        await sock.send_msg(server_ip, server_port, query)
        logger.info(f"[{server_name}] Telegram: <<< {m.from_user.username}: {m.text} >>>")
