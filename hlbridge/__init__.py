import logging
import time
import re

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import BadRequest
from hydrogram.raw.all import layer

from .utils import (
    HLServer,
    Utils,
    Socket
)

from .config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    WORKERS,
    SERVERS
)

from subprocess import run

__commit__ = (
    run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, check=False)
    .stdout.decode()
    .strip()
    or "None"
)

__version_number__ = (
    run(["git", "rev-list", "--count", "HEAD"], capture_output=True, check=False)
    .stdout.decode()
    .strip()
    or "0"
)

logger = logging.getLogger(__name__)

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

    async def start(self):
        await super().start()

        self.start_time = time.time()

        logger.info(
            "HLBridge running with Hydrogram v%s (Layer %s) started on @%s.",
            hydrogram.__version__,
            layer,
            self.me.username,
        )

        start_message = (
            "<b>HLBridge started!</b>\n\n"
            f"<b>Version number:</b> <code>r{__version_number__} ({__commit__})</code>\n"
            f"<b>Hydrogram:</b> <code>v{hydrogram.__version__}</code>"
        )

        try:
            for server in SERVERS:
                await self.send_message(chat_id=server['chat_id'], text=start_message)
        except BadRequest:
            logger.warning(f"Unable to send message, check if <chat_id: {server['chat_id']}> is correct ")

    async def send_to_telegram(self, sock, log_prefix, chat_id, server_name, log_suicides, log_kills ):
        while True:
                l = await sock.receive()
                l = l[4:].decode(errors='replace').replace('\n', '')
                l = Utils.remove_color_tags(l)

                saymatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" say "(.*)"')
                entermatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" entered the game')
                disconnectmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" disconnected')
                suicidematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" committed suicide with "(.*)"')
                waskilledmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" committed suicide with "(.*)" \(.*\)')
                killedmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" killed "(.*)<[^>]+><(.*)><[^>]+>" with "(.*)"')
                kickmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Kick: "(.*)<[^>]+><(.*)><>" was kicked by "(.*)" \(message "(.*)"\)')
                changematch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><[^>]+>" changed name to "(.*)"')
                startedmapmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: Started map "(.*?)"')
                connectedmatch = re.compile(fr'{log_prefix} \d\d\/\d\d\/\d\d\d\d - \d\d\:\d\d\:\d\d\: "(.*)<[^>]+><(.*)><>" connected, address "([^"]+)"')

                matches = [
                    (saymatch, lambda g: f'{g[0]}: {g[2]}'),
                    (suicidematch, lambda g: f'"{g[0]}" committed suicide with "{g[2]}"' if log_suicides == 1 else None),
                    (waskilledmatch, lambda g: f'"{g[0]}" committed suicide with "{g[2]}"' if log_suicides == 1 else None),
                    (killedmatch, lambda g: f'"{g[0]}" killed "{g[2]}" with "{g[4]}"' if log_kills == 1 else None),
                    (kickmatch, lambda g: f'Player "{g[0]}" was kicked with message: "{g[3]}"'),
                    (changematch, lambda g: f'Player "{g[0]}" changed name to: "{g[2]}"'),
                    (entermatch, lambda g: f'Player "{g[0]}" has joined the game'),
                    (disconnectmatch, lambda g: f'Player "{g[0]}" has left the game'),
                    (startedmapmatch, lambda g: f'Started map "{g[0]}"'),
                    (connectedmatch, lambda g: f'Player "{g[0]}" connected')
                ]

                for pattern, formatter in matches:
                    m = pattern.match(l)
                    if m:
                        g = m.groups()
                        text = formatter(g)
                        if text:  # Only send message if formatting function returned a valid text
                            await self.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True, disable_notification=True)
                            print(f"[{Utils.get_current_time()}] [{server_name}] Half-Life: <<< {text} >>>")


    async def stop(self):
        await super().stop()
        logger.warning("HLBridge stopped!")
