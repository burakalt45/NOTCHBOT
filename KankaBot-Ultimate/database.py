import aiosqlite

DATABASE="bot.db"

async def init():

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute("""

CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY,

username TEXT,

name TEXT,

coins INTEGER DEFAULT 1000,

xp INTEGER DEFAULT 0,

level INTEGER DEFAULT 1

)

""")

        await db.commit()
