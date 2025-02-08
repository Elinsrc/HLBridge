import sys
import asyncio
import logging
import platform
import argparse

from hydrogram import idle
from hlbridge import HLBridge

from .utils import (
    HLServer,
    Utils,
    Socket
)

from .envars import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    CHAT_ID,
    OWNER,
    LOG_PORT,
    SERVER_IP,
    SERVER_PORT,
    RCON_PASSWD,
    CONNECTIONLESS_ARGS
)

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)

logging.getLogger("hydrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("uvloop is not installed and therefore will be disabled.")

async def start_bot():
    hlbridge = HLBridge()
    sock = Socket()

    try:
        await sock.connect(LOG_PORT)
        await hlbridge.start()
        sock_task = asyncio.create_task(hlbridge.send_to_telegram(sock, log_prefix))
        await idle()
    except KeyboardInterrupt:
        logger.warning("Forced stop!")
    finally:
        sock_task.cancel()
        await hlbridge.stop()
        await sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HLBridge is a bot that forwards player messages from Telegram to the Half-Life server and vice versa.")
    parser.add_argument("--oldengine", action='store_true', help="enable read old engine log")
    args = parser.parse_args()

    if args.oldengine:
        protocol = 48
        log_prefix = "log L"
    else:
        protocol = 49
        log_prefix = "log"

    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(start_bot())

    event_loop.close()
