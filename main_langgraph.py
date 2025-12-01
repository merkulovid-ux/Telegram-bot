import asyncio
import logging
import os
import sys
from typing import Dict

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from analytics import log_event
from config import TELEGRAM_BOT_TOKEN
from langgraph_app import build_graph

# In-memory checkpoints per user (replace with Redis/DB if needed)
user_checkpointers: Dict[int, MemorySaver] = {}


async def langgraph_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_checkpointers:
        user_checkpointers[user_id] = MemorySaver()

    app = build_graph(user_checkpointers[user_id])
    inputs = {
        "input_message": message,
        "messages": [HumanMessage(content=message.text)],
    }
    config = {"configurable": {"thread_id": str(user_id)}}

    try:
        await app.ainvoke(inputs, config)
    except Exception:
        logging.exception("langgraph_handler failed")
        await message.answer("Service temporarily unavailable, please try again later.")


async def callback_query_handler(query: types.CallbackQuery):
    user_id = query.from_user.id

    if user_id not in user_checkpointers:
        user_checkpointers[user_id] = MemorySaver()

    app = build_graph(user_checkpointers[user_id])
    inputs = {
        "input_message": query.message,
        "messages": [HumanMessage(content=query.data)],
    }
    config = {"configurable": {"thread_id": str(user_id)}}

    try:
        await app.ainvoke(inputs, config)
    except Exception:
        logging.exception("callback_query_handler failed")
        await query.message.answer("Service temporarily unavailable, please try again later.")
    await query.answer()


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(langgraph_handler, F.text & ~F.text.startswith("/start"))
    dp.callback_query.register(callback_query_handler)

    @dp.message(CommandStart())
    async def command_start_handler(message: types.Message):
        try:
            await log_event(message.from_user.id, "/start", message.text)
        except Exception:
            logging.warning("log_event failed on /start")
        welcome_message = (
            f"Привет, <b>{message.from_user.full_name}</b>! "
            "Это бот ProcessOff. Доступные команды: /ask, /digest, /swot, /nvc, "
            "/po_helper, /conflict, /retro, /icebreaker, /kb, /feedback."
        )
        await message.answer(welcome_message, parse_mode="HTML")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
