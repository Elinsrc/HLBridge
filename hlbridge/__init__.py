# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

import asyncio
import re
import time
from typing import Dict, List, Optional

from loguru import logger

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import BadRequest
from hydrogram.raw.all import layer

from .utils import (
    Socket,
    remove_color_tags,
    get_version_number,
    get_commit
)

from .config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    WORKERS
)


class HLBridge(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            parse_mode=ParseMode.HTML,
            workers=WORKERS,
            plugins={"root": "hlbridge.plugins"},
            sleep_threshold=180,
        )
        self.server_tasks: Dict[str, asyncio.Task] = {}
        self.server_sockets: Dict[str, Socket] = {}
        self.chat_id: Optional[int] = None
        self.topic_id: Optional[int] = None

    async def start(self):
        from .database.settings import get_settings
        from .database.servers import get_servers
        await super().start()

        self.start_time = time.time()

        logger.info(f"HLBridge running with Hydrogram v{hydrogram.__version__} (Layer {layer}) started on @{self.me.username}.")

        while True:
            settings = await get_settings()
            if settings and settings["chat_id"] and settings["topic_id"]:
                self.chat_id = settings["chat_id"]
                self.topic_id = settings["topic_id"]
                break
            logger.info("CHAT_ID and TOPIC_ID is not configured. Waiting for /setup")
            await asyncio.sleep(5)

        start_message = (
            "<b>HLBridge started!</b>\n\n"
            f"<b>Version number:</b> <code>r{get_version_number()} ({get_commit()})</code>\n"
            f"<b>Hydrogram:</b> <code>v{hydrogram.__version__}</code>"
        )

        await self.send_message(chat_id=self.chat_id, text=start_message, message_thread_id=self.topic_id)

        servers = await get_servers(active_only=True)
        for server in servers:
            await self.start_server_monitoring(server)

    async def send_to_telegram(self, sock: Socket, log_prefix: str, topic_id: int, server_name: str):
        while True:
                l = await sock.receive()
                l = l[4:].decode(errors='replace').replace('\n', '')
                l = remove_color_tags(l)

                saymatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" say "(.*)"')
                # entermatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" entered the game')
                # disconnectmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" disconnected')
                # suicidematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" committed suicide with "(.*)"')
                # waskilledmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" committed suicide with "(.*)" \(.*\)')
                # killedmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" killed "(.*)<[^>]+><(.*)><[^>]+>" with "(.*)"')
                # kickmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Kick: "(.*)<[^>]+><(.*)><>" was kicked by "(.*)" \(message "(.*)"\)')
                # changematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" changed name to "(.*)"')
                # startedmapmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Started map "(.*?)"')
                # connectedmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><>" connected, address "([^"]+)"')

                # matches = [
                #     (saymatch, lambda g: f'{g[0]}: {g[2]}'),
                #     (suicidematch, lambda g: f'"{g[0]}" committed suicide with "{g[2]}"'),
                #     (waskilledmatch, lambda g: f'"{g[0]}" committed suicide with "{g[2]}"'),
                #     (killedmatch, lambda g: f'"{g[0]}" killed "{g[2]}" with "{g[4]}"',
                #     (kickmatch, lambda g: f'Player "{g[0]}" was kicked with message: "{g[3]}"'),
                #     (changematch, lambda g: f'Player "{g[0]}" changed name to: "{g[2]}"'),
                #     (entermatch, lambda g: f'Player "{g[0]}" has joined the game'),
                #     (disconnectmatch, lambda g: f'Player "{g[0]}" has left the game'),
                #     (startedmapmatch, lambda g: f'Started map "{g[0]}"'),
                #     (connectedmatch, lambda g: f'Player "{g[0]}" connected')
                # ]

                # for pattern, formatter in matches:
                #     m = pattern.match(l)
                #     if m:
                #         g = m.groups()
                #         text = formatter(g)
                #         if text:  # Only send message if formatting function returned a valid text
                #             await self.send_message(chat_id=self.chat_id, text=text, message_thread_id=topic_id, disable_web_page_preview=True, disable_notification=True)
                #             logger.info(f"[{server_name}] <<< {text} >>>")


                m = saymatch.match(l)
                if m:
                    g = m.groups()
                    text = f'{g[0]}: {g[2]}'
                    await self.send_message(chat_id=self.chat_id, text=text, message_thread_id=topic_id, disable_web_page_preview=True, disable_notification=True)
                    logger.info(f"[{server_name}] <<< {text} >>>")

    async def start_server_monitoring(self, server: Dict) -> bool:
        server_name = server["server_name"]
        if server_name in self.server_tasks:
            await self.stop_server_monitoring(server_name)

        sock = Socket()
        await sock.connect("0.0.0.0", server["log_port"])
        log_prefix = "log" if server["protocol"] == 49 else "log L"

        task = asyncio.create_task(self.send_to_telegram(sock, log_prefix, server["topic_id"], server_name))

        self.server_tasks[server_name] = task
        self.server_sockets[server_name] = sock
        return True

    async def stop_server_monitoring(self, server_name: str) -> bool:
        if server_name in self.server_tasks:
            task = self.server_tasks.pop(server_name)
            task.cancel()

        if server_name in self.server_sockets:
            sock = self.server_sockets.pop(server_name)
            await sock.close()

        return True

    async def restart_monitoring(self, servers: Optional[List[Dict]] = None):
        if servers is None:
            servers = await get_servers(active_only=True)

        stopped_count = 0
        started_count = 0

        for name in list(self.server_tasks.keys()):
            if await self.stop_server_monitoring(name):
                stopped_count += 1

        for server in servers:
            if await self.start_server_monitoring(server):
                started_count += 1

        return stopped_count, started_count


    async def stop(self):
        for name in list(self.server_tasks.keys()):
            await self.stop_server_monitoring(name)
        await super().stop()
        logger.warning("HLBridge stopped!")
