# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Elinsrc

from typing import Dict, List, Optional
from .core import database

conn = database.get_conn()

async def add_server(server: Dict) -> None:
    await conn.execute(
        """
        INSERT INTO servers (
            server_name, port, log_port, oldengine, topic_id,
            connectionless_args, rcon_password, log_suicides, log_kills
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            server['server_name'],
            server['port'],
            server['log_port'],
            server['oldengine'],
            server['topic_id'],
            server['connectionless_args'],
            server['rcon_password'],
            server['log_suicides'],
            server['log_kills']
        )
    )
    await conn.commit()


async def update_server(server_name: str, updates: Dict) -> None:
    set_clauses = []
    params = []

    for key, value in updates.items():
        if key != 'server_name':
            set_clauses.append(f"{key} = ?")
            params.append(value)

    if not set_clauses:
        return

    params.append(server_name)
    query = f"UPDATE servers SET {', '.join(set_clauses)} WHERE server_name = ?"
    await conn.execute(query, params)
    await conn.commit()


async def remove_server(server_name: str) -> None:
    await conn.execute(
        "DELETE FROM servers WHERE server_name = ?", (server_name,)
    )
    await conn.commit()


async def toggle_server(server_name: str) -> Optional[str]:
    cursor = await conn.execute(
        "SELECT is_active FROM servers WHERE server_name = ?", (server_name,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if not row:
        return None

    new_status = 0 if row['is_active'] == 1 else 1
    await conn.execute(
        "UPDATE servers SET is_active = ? WHERE server_name = ?",
        (new_status, server_name)
    )
    await conn.commit()

    return "activated" if new_status else "deactivated"


async def get_server(server_name: str) -> Optional[Dict]:
    cursor = await conn.execute(
        "SELECT * FROM servers WHERE server_name = ?", (server_name,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    return dict(row) if row else None


async def get_servers(active_only: bool = False) -> List[Dict]:
    query = "SELECT * FROM servers"
    params = ()

    if active_only:
        query += " WHERE is_active = 1"

    query += " ORDER BY server_name"

    cursor = await conn.execute(query, params)
    rows = await cursor.fetchall()
    await cursor.close()

    return [dict(row) for row in rows]
