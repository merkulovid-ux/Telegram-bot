import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_db_pool
from analytics import log_event

class AdminState(StatesGroup):
    dashboard_main = State()
    browsing_feedback = State()

router = Router()

ADMIN_ID = 182868329
FEEDBACK_PER_PAGE = 5

# --- Функции рендеринга ---

async def get_stats_text(conn) -> str:
    total_users = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM events")
    dau = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM events WHERE timestamp >= $1", datetime.date.today())
    
    command_counts_rows = await conn.fetch("SELECT command, COUNT(*) as count FROM events GROUP BY command ORDER BY count DESC")
    command_counts = "\n".join([f"- `{row['command']}`: {row['count']}" for row in command_counts_rows])

    return f"""<b>📊 Статистика использования:</b>

<b>Пользователи:</b>
- Всего: {total_users}
- Активных сегодня: {dau}

<b>Популярность команд:</b>
{command_counts}"""

async def get_feedback_text_and_keyboard(conn, page: int) -> tuple[str, InlineKeyboardMarkup]:
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

# --- Обработчики ---

async def show_main_dashboard(message: Message, conn):
    stats_text = await get_stats_text(conn)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="admin_main")],
        [InlineKeyboardButton(text="📝 Посмотреть отзывы", callback_data="admin_feedback_0")]
    ])
    await message.edit_text(stats_text, reply_markup=keyboard, parse_mode='HTML')

@router.message(Command("admin"))
async def admin_dashboard_handler(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await log_event(message.from_user.id, '/admin', '')
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        stats_text = await get_stats_text(conn)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="admin_main")],
            [InlineKeyboardButton(text="📝 Посмотреть отзывы", callback_data="admin_feedback_0")]
        ])
        await message.answer(stats_text, reply_markup=keyboard, parse_mode='HTML')
    await state.set_state(AdminState.dashboard_main)

@router.callback_query(AdminState.dashboard_main, F.data == "admin_main")
async def refresh_stats_handler(callback_query: CallbackQuery, state: FSMContext):
    await log_event(callback_query.from_user.id, 'admin_refresh_stats', '')
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await show_main_dashboard(callback_query.message, conn)
    await callback_query.answer("Статистика обновлена")

@router.callback_query(F.data.startswith("admin_feedback_"))
async def view_feedback_handler(callback_query: CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split("_")[2])
    await log_event(callback_query.from_user.id, 'admin_view_feedback', f"page_{page}")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        feedback_text, keyboard = await get_feedback_text_and_keyboard(conn, page)
        await callback_query.message.edit_text(feedback_text, reply_markup=keyboard, parse_mode='HTML')
    
    await state.set_state(AdminState.browsing_feedback)
    await callback_query.answer()

@router.callback_query(AdminState.browsing_feedback, F.data == "admin_main")
async def back_to_main_handler(callback_query: CallbackQuery, state: FSMContext):
    await log_event(callback_query.from_user.id, 'admin_back_to_main', '')
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await show_main_dashboard(callback_query.message, conn)
    await state.set_state(AdminState.dashboard_main)
    await callback_query.answer()
