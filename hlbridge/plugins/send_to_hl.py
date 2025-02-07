from hydrogram import Client, filters
from hydrogram.types import Message

from hlbridge.utils import Utils, Socket
from hlbridge.envars import (
    CHAT_ID,
    SERVER_IP,
    SERVER_PORT,
    CONNECTIONLESS_ARGS
)

@Client.on_message(filters.chat(CHAT_ID) & ~filters.command(["status","id"]))
async def send_to_hl(c: Client, m: Message):
    sock = Socket()
    msg = f"(telegram) {m.from_user.username}: {m.text}"
    query = b'\xff\xff\xff\xff%b %b\n' % (CONNECTIONLESS_ARGS.encode(), msg.encode("utf8"))
    await sock.send_msg(SERVER_IP, SERVER_PORT, query)
    print(f"[{Utils.get_current_time()}] Telegram: <<< {m.from_user.username}: {m.text} >>>")
