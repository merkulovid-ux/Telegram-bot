import asyncio
import logging
import sys
import os

# Добавляем корневую директорию в sys.path для корректного импорта
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aiogram import Bot, Dispatcher

from config import TELEGRAM_BOT_TOKEN
from db import DB_POOL, get_db_pool
from handlers import router as main_router # Импортируем только главный роутер

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем только главный роутер
    dp.include_router(main_router)

    # Инициализируем и закрываем пул соединений
    await get_db_pool()
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if DB_POOL:
            await DB_POOL.close()

if __name__ == "__main__":
    asyncio.run(main())
