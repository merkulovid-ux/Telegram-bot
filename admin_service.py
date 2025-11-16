# admin_service.py
import datetime
from db import get_db_pool
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID
...
# ADMIN_ID = 182868329 # Замените на ваш ID администратора
FEEDBACK_PER_PAGE = 5

async def get_stats_text() -> str:
    """
    Формирует текст со статистикой использования бота.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM events")
        dau = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM events WHERE timestamp >= $1", datetime.date.today())
        
        command_counts_rows = await conn.fetch("SELECT command, COUNT(*) as count FROM events GROUP BY command ORDER BY count DESC")
        command_counts = "\n".join([f"- `{row['command']}`: {row['count']}" for row in command_counts_rows])

    return f"""
<b>📊 Статистика использования:</b>

<b>Пользователи:</b>
- Всего: {total_users}
- Активных сегодня: {dau}

<b>Популярность команд:</b>
{command_counts}"""

async def get_feedback_text_and_keyboard(page: int) -> tuple[str, InlineKeyboardMarkup]:
    """
    Формирует текст с отзывами и клавиатуру для пагинации.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        offset = page * FEEDBACK_PER_PAGE
        total_feedback = await conn.fetchval("SELECT COUNT(*) FROM feedback")
        
        feedback_rows = await conn.fetch(
            "SELECT feedback_text, timestamp FROM feedback ORDER BY timestamp DESC LIMIT $1 OFFSET $2",
            FEEDBACK_PER_PAGE, offset
        )

    if not feedback_rows:
        return "Отзывов пока нет.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад к статистике", callback_data="admin_main")]])

    feedback_text = "<b>📝 Последние отзывы:</b>\n\n"
    for row in feedback_rows:
        ts = row['timestamp'].strftime("%Y-%m-%d %H:%M")
        feedback_text += f"<i>От {ts}:</i>\n{row['feedback_text']}\n\n"

    # Кнопки пагинации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Ранее", callback_data=f"admin_feedback_{page - 1}"))
    if (page + 1) * FEEDBACK_PER_PAGE < total_feedback:
        nav_buttons.append(InlineKeyboardButton(text="Позднее ➡️", callback_data=f"admin_feedback_{page + 1}"))

    keyboard_rows = [nav_buttons] if nav_buttons else []
    keyboard_rows.append([InlineKeyboardButton(text="↩️ Назад к статистике", callback_data="admin_main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    return feedback_text, keyboard
