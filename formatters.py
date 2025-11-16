# formatters.py
import html
import re
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

DEFAULT_FALLBACK = "Извините, не удалось получить ответ. Попробуйте позже."

def markdown_to_html(raw: str) -> str:
    """
    Преобразует Markdown в HTML для отправки в Telegram.
    """
    safe = html.escape(raw.strip()) or DEFAULT_FALLBACK
    safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
    safe = re.sub(r'(?m)^(\*|-)\s+(.*)', "\u2022 \2", safe)
    safe = re.sub(r'(?m)^#{1,6}\s+(.*)', r'<b>\1</b>', safe)
    return safe

def follow_up_markup() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для follow-up вопросов.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ещё")],
            [KeyboardButton(text="Уточнить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def format_citations(titles: list[str]) -> str:
    """
    Форматирует заголовки источников для отправки в Telegram.
    """
    if not titles:
        return ""

    shown = titles[:5]
    suffix = "" if len(titles) <= 5 else "\n…и другие источники."
    lines = "\n".join(f"• {title}" for title in shown)
    return f"<b>Источники:</b>\n{lines}{suffix}"
