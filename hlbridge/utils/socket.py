# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

import asyncio
import asyncio_dgram
from typing import Union
from loguru import logger


class Socket:
    def __init__(self):
        self.sock = None

    async def connect(self, ip, port):
        self.sock = await asyncio_dgram.bind((ip, port))
        logger.info(f"Socket bound to {ip}:{port}")

    async def receive(self):
        if self.sock is None:
            logger.error("Socket is not connected!")
            return

        data, _ = await self.sock.recv()
        return data

    async def send_packet(self, ip, port, msg, timeout: float) -> Union[bytes, None]:
        stream = await asyncio_dgram.connect((ip, port))
        await stream.send(msg)
        try:
            data, _ = await asyncio.wait_for(stream.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            data = None
        finally:
            stream.close()

        return data

    async def send_msg(self, ip, port, msg):
        stream = await asyncio_dgram.connect((ip, port))
        await stream.send(msg)
        stream.close()

    async def close(self):
        if self.sock is not None:
            self.sock.close()
            logger.info("Socket closed!")
