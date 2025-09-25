# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from .core import database

conn = database.get_conn()


async def set_settings(owner_id: int, chat_id: int, topic_id: int):
    await conn.execute(
        """
        INSERT INTO bot_settings (owner_id, chat_id, topic_id)
        VALUES (?, ?, ?)
        ON CONFLICT(owner_id) DO UPDATE SET
            chat_id = excluded.chat_id,
            topic_id = excluded.topic_id
        """,
        (owner_id, chat_id, topic_id),
    )
    await conn.commit()


async def get_settings():
    cursor = await conn.execute("SELECT owner_id, chat_id, topic_id FROM bot_settings LIMIT 1")
    row = await cursor.fetchone()
    await cursor.close()
    if row:
        return {"owner_id": row["owner_id"], "chat_id": row["chat_id"], "topic_id": row["topic_id"]}
    return None


async def user_owner(user_id: int) -> bool:
    cursor = await conn.execute("SELECT owner_id FROM bot_settings LIMIT 1")
    row = await cursor.fetchone()
    await cursor.close()
    return row is not None and row[0] == user_id
