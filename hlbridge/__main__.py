import sys
import asyncio
import logging
from loguru import logger
import platform

from hydrogram import idle
from hlbridge import HLBridge

from .utils import (
    HLServer,
    Utils,
    Socket,
    InterceptHandler
)

from .config import SERVERS


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("hydrogram.syncer").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)
logger.remove()
logger.add(
    sys.stdout,
    format="[<green>{time:YYYY-MM-DD HH:mm:ss}</green>] "
           "[<level>{level}</level>] "
           "<white>{name}</white>.<white>{function}</white>: "
           "<level>{message}</level>",
    level="INFO",
    colorize=True,
)


logger = logging.getLogger(__name__)


try:
    import uvloop

    uvloop.install()
except ImportError:
    if platform.system() != "Windows":
        logger.warning("uvloop is not installed and therefore will be disabled.")


async def start_bot():
    hlbridge = HLBridge()
    sock_tasks = []

    try:
        await hlbridge.start()

        for server in SERVERS:
            sock = Socket()
            await sock.connect(server['log_port'])
            log_prefix = "log L" if server['oldengine'] == 1 else "log"
            sock_task = asyncio.create_task(hlbridge.send_to_telegram(
                sock,
                log_prefix,
                server['topic_id'],
                server['server_name'],
                server['log_suicides'],
                server['log_kills']
                ))
            sock_tasks.append((sock, sock_task))

        await idle()

    except KeyboardInterrupt:
        logger.warning("Forced stop!")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        for sock, sock_task in sock_tasks:
            sock_task.cancel()
            try:
                await sock_task
            except asyncio.CancelledError:
                pass
            finally:
                try:
                    await sock.close()
                except Exception as e:
                    logger.error(f"Error closing socket: {e}")

        await hlbridge.stop()


if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(start_bot())

    event_loop.close()
