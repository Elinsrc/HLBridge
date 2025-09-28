# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC
# Copyright (c) 2025 Elinsrc

from loguru import logger

import aiosqlite


class Database:
    def __init__(self):
        self.conn: aiosqlite.Connection = None
        self.path: str = "hlbridge.db"
        self.is_connected: bool = False

    async def connect(self):
        # Open the connection
        conn = await aiosqlite.connect(self.path)

        # Define the tables
        await conn.executescript(
            """
        CREATE TABLE IF NOT EXISTS groups(
            chat_id INTEGER PRIMARY KEY,
            chat_lang TEXT
        );

        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            chat_lang TEXT
        );

        CREATE TABLE IF NOT EXISTS channels(
            chat_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS servers(
            server_name TEXT,
            port INTEGER,
            log_port INTEGER,
            oldengine INTEGER DEFAULT 0,
            topic_id INTEGER,
            connectionless_args TEXT,
            rcon_password TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS bot_settings(
            owner_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            topic_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS admins(
            user_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS user_names(
            user_id INTEGER PRIMARY KEY,
            default_name TEXT,
            custom_name TEXT
        );
        """
        )

        # Enable VACUUM
        await conn.execute("VACUUM")

        # Enable WAL
        await conn.execute("PRAGMA journal_mode=WAL")

        # Update the database
        await conn.commit()

        conn.row_factory = aiosqlite.Row

        self.conn = conn
        self.is_connected: bool = True

        logger.info("The database has been connected.")

    async def close(self):
        # Close the connection
        await self.conn.close()

        self.is_connected: bool = False

        logger.info("The database was closed.")

    def get_conn(self) -> aiosqlite.Connection:
        if not self.is_connected:
            raise RuntimeError("The database is not connected.")

        return self.conn


database = Database()
