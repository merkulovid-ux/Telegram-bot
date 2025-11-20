import asyncio
import logging
import sys
import os
from typing import Dict

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from config import TELEGRAM_BOT_TOKEN
from langgraph_app import build_graph
from analytics import log_event

# Глобальный словарь для хранения чекпоинтеров для каждого пользователя
# В реальном приложении это должно быть персистентное хранилище (Redis, DB)
user_checkpointers: Dict[int, MemorySaver] = {}

async def langgraph_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Получаем или создаем чекпоинтер для пользователя
    if user_id not in user_checkpointers:
        user_checkpointers[user_id] = MemorySaver()
    
    checkpointer = user_checkpointers[user_id]
    
    # Собираем граф с чекпоинтером
    app = build_graph(checkpointer)

    # Входные данные для графа
    inputs = {
        "input_message": message,
        "messages": [HumanMessage(content=message.text)],
    }
    
    # ID диалога, чтобы LangGraph мог сохранять и восстанавливать состояние
    config = {"configurable": {"thread_id": str(user_id)}}

    # Асинхронно запускаем граф
    await app.ainvoke(inputs, config)

async def callback_query_handler(query: types.CallbackQuery):
    user_id = query.from_user.id
    
    # Получаем или создаем чекпоинтер для пользователя
    if user_id not in user_checkpointers:
        user_checkpointers[user_id] = MemorySaver()
    
    checkpointer = user_checkpointers[user_id]
    
    # Собираем граф с чекпоинтером
    app = build_graph(checkpointer)

    # Входные данные для графа
    # Важно: мы передаем исходное сообщение, чтобы иметь возможность его редактировать
    inputs = {
        "input_message": query.message, 
        "messages": [HumanMessage(content=query.data)],
    }
    
    # ID диалога, чтобы LangGraph мог сохранять и восстанавливать состояние
    config = {"configurable": {"thread_id": str(user_id)}}

    # Асинхронно запускаем граф
    await app.ainvoke(inputs, config)
    await query.answer() # Отвечаем на callback, чтобы убрать "часики"

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(langgraph_handler, F.text & ~F.text.startswith('/start'))
    dp.callback_query.register(callback_query_handler) # Регистрируем обработчик
    
    @dp.message(CommandStart())
    async def command_start_handler(message: types.Message):
        await log_event(message.from_user.id, "/start", message.text)
        welcome_message = (
            f"Привет, <b>{message.from_user.full_name}</b>! 👋 Я бот ProcessOff — помощник по управлению продуктами и командами.\n\n"
            "Моя архитектура построена на `LangGraph`.\n\n"
            "Вот что я умею:\n\n"
            "<b>/ask</b> — задайте вопрос и получите ответ из базы. Примеры:\n"
            "<code>/ask как Product Owner работает с командой?</code>\n"
            "<code>/ask как строить дорожную карту?</code>\n\n"
            "<b>/digest</b> — краткий дайджест (3-5 тезисов): <code>/digest роли в Scrum</code>\n\n"
            "<b>/swot</b> — SWOT-анализ ситуации: <code>/swot открытие кофейни</code>\n\n"
            "<b>/nvc</b> — помогу сформулировать послание в духе Ненасильственного общения.\n"
            "<b>/po_helper</b> — инструменты Product Owner.\n"
            "<b>/conflict</b> — медиативная сессия по конфликту.\n\n"
            "<b>/kb</b> — просмотр базы знаний.\n\n"
            "Подписывайтесь на канал <b>PRO Менеджмент и коучинг</b>: https://t.me/processoff"
        )
        await message.answer(welcome_message, parse_mode="HTML")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        pass

if __name__ == "__main__":
    asyncio.run(main())
