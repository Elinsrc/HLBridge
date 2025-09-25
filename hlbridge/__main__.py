# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

import sys
import asyncio
import logging
from loguru import logger
import platform

from hydrogram import idle
from hlbridge import HLBridge

from .database import database

from .utils import (
    HLServer,
    Socket,
    InterceptHandler
)


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


async def monitor_config_changes(hlbridge: HLBridge, interval: int = 1):
    last_config_hash = None

    while True:
        try:
            from .database.servers import get_servers
            servers = await get_servers(active_only=True)

            config_hash = hash(str(sorted([tuple(s.items()) for s in servers])))

            if last_config_hash is None:
                last_config_hash = config_hash
            elif config_hash != last_config_hash:
                logger.info("Server configuration changed. Reloading...")
                stopped, started = await hlbridge.restart_monitoring(servers)
                logger.info(f"Updated server monitoring: {started} servers started, {stopped} stopped")
                last_config_hash = config_hash

        except Exception as e:
            logger.error(f"Error monitoring config changes: {e}")

        await asyncio.sleep(interval)


async def start_bot():
    hlbridge = HLBridge()
    try:
        await database.connect()

        from .database.servers import get_servers
        servers = await get_servers(active_only=True)

        await hlbridge.start()

        logger.info(f"Starting monitoring for {len(servers)} active servers...")
        asyncio.create_task(monitor_config_changes(hlbridge))

        await idle()

    except KeyboardInterrupt:
        logger.warning("Forced stop!")
    finally:
        await hlbridge.stop()
        if database.is_connected:
            await database.close()


if __name__ == "__main__":
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(start_bot())

    event_loop.close()
