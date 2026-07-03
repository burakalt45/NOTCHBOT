from __future__ import annotations

import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "bot.db"


class Database:

    def __init__(self, path: Path = DB_PATH):
        self.path = path

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:

        conn = await aiosqlite.connect(self.path)

        conn.row_factory = aiosqlite.Row

        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        await conn.execute("PRAGMA synchronous=NORMAL;")

        try:
            yield conn
            await conn.commit()

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    async def execute(self, query: str, *params):

        async with self.connection() as conn:
            await conn.execute(query, params)

    async def executemany(self, query: str, values):

        async with self.connection() as conn:
            await conn.executemany(query, values)

    async def fetchone(self, query: str, *params):

        async with self.connection() as conn:

            cursor = await conn.execute(query, params)

            return await cursor.fetchone()

    async def fetchall(self, query: str, *params):

        async with self.connection() as conn:

            cursor = await conn.execute(query, params)

            return await cursor.fetchall()

    async def fetchval(self, query: str, *params):

        row = await self.fetchone(query, *params)

        if row is None:
            return None

        return row[0]


db = Database()
