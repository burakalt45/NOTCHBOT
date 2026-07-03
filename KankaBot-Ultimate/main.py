from telegram.ext import Application

from config import BOT_TOKEN

from database import init

import asyncio

async def startup(app):

    await init()

async def main():

    app = Application.builder().token(BOT_TOKEN).post_init(startup).build()

    app.run_polling()

if __name__=="__main__":

    asyncio.run(main())
