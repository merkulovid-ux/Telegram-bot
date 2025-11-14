from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from analytics import log_event


router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    await log_event(message.from_user.id, "/start", message.text)
    welcome_message = f"Привет, <b>{message.from_user.full_name}</b>! 👋 Я бот ProcessOff — помощник по управлению продуктами и командам.\n\n"
    welcome_message += "Вот что умею:\n\n"
    welcome_message += "<b>/kb</b> — расскажу, какие темы уже загружены в базу знаний.\n\n"
    welcome_message += "<b>/ask</b> — задайте вопрос и получите ответ из базы. Примеры:\n"
    welcome_message += "<code>/ask как Product Owner работает с командой?</code>\n"
    welcome_message += "<code>/ask как строить дорожную карту?</code>\n\n"
    welcome_message += "<b>/digest</b> — краткий дайджест (3-5 тезисов): <code>/digest роли в Scrum</code>\n\n"
    welcome_message += "<b>/swot</b> — SWOT-анализ ситуации: <code>/swot открытие кофейни</code>\n\n"
    welcome_message += "<b>/nvc</b> — помогу сформулировать послание в духе Ненасильственного общения.\n"
    welcome_message += "<b>/po_helper</b> — инструменты Product Owner.\n"
    welcome_message += "<b>/conflict</b> — медиативная сессия по конфликту.\n\n"
    welcome_message += "/retro — идеи для ретроспективы.\n"
    welcome_message += "/icebreaker — короткие командные активности.\n\n"
    welcome_message += "Подписывайтесь на канал <b>PRO Менеджмент и коучинг</b>: https://t.me/processoff"
    await message.answer(welcome_message, parse_mode="HTML")
