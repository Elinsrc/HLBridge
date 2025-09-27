# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from .core import database

conn = database.get_conn()


async def set_user_name(user_id: int, default_name: str, custom_name: str):
    await conn.execute(
        '''
        INSERT INTO user_names (user_id, default_name, custom_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            default_name=excluded.default_name,
            custom_name=excluded.custom_name
        ''',
        (user_id, default_name, custom_name)
    )
    await conn.commit()


async def remove_user_name(user_id: int):
    await conn.execute('DELETE FROM user_names WHERE user_id = ?', (user_id,))
    await conn.commit()


async def get_user_name(user_id: int) -> str:
    cursor = await conn.execute(
        'SELECT custom_name FROM user_names WHERE user_id = ?', (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    return row[0] if row else None


async def get_all_user_names():
    cursor = await conn.execute('SELECT user_id, default_name, custom_name FROM user_names')
    rows = await cursor.fetchall()
    await cursor.close()
    return rows
