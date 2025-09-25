# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from .core import database

conn = database.get_conn()


async def add_to_admin(user_id: int):
    await conn.execute('INSERT INTO admins (user_id) VALUES (?)', (user_id,))
    await conn.commit()


async def remove_from_admin(user_id: int):
    await conn.execute('DELETE FROM adminsWHERE user_id = ?', (user_id,))
    await conn.commit()


async def user_admin(user_id: int) -> bool:
    cursor = await conn.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row is not None
