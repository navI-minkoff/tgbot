import asyncio
import sys
import logging

from aiogram import Bot, Dispatcher

from app.handlers import router
from dotenv import load_dotenv
import os
from app.database.models import async_main


async def main():
    await async_main()
    load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Exit')
