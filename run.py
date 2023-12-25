import asyncio
import sys
import logging

from aiogram import Bot, Dispatcher

from app.admin import create_backup
from app.handlers import router
from dotenv import load_dotenv
import os
from app.database.models import async_main
from datetime import datetime


async def scheduler():
    while True:
        local_file_path = "C:/programms/BD/tgbot/db.sqlite3"
        remote_file_path = f"backup/back_up_{datetime.now()}.sqlite3"
        await create_backup(local_file_path, remote_file_path)
        await asyncio.sleep(1 * 60 * 60 * 24)


async def main():
    await async_main()
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')

    dp = Dispatcher()
    dp.include_router(router)
    loop = asyncio.get_event_loop()

    loop.create_task(scheduler())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Exit')
