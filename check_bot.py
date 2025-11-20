import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def check_bot_status():
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN не найден в .env файле.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        # Проверяем токен и получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"Бот успешно подключен! Имя: @{bot_info.username}, ID: {bot_info.id}")

        # Удаляем вебхуки и очищаем ожидающие обновления
        await bot.delete_webhook(drop_pending_updates=True)
        print("Вебхуки удалены, ожидающие обновления очищены.")

        # Проверяем, есть ли еще обновления
        updates = await bot.get_updates(offset=-1, limit=1)
        if updates:
            print(f"Внимание: После очистки все еще есть обновления. Последнее обновление: {updates[0].update_id}")
        else:
            print("Ожидающих обновлений нет.")

    except Exception as e:
        print(f"Ошибка при подключении к Telegram API: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_bot_status())
