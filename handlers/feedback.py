from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_db_pool
from analytics import log_event

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

router = Router()
ADMIN_ID = 182868329 # Ваш ID

@router.message(Command("feedback"))
async def feedback_handler(message: Message, state: FSMContext):
    await log_event(message.from_user.id, '/feedback', message.text)
    await message.answer("Я внимательно вас слушаю. Пожалуйста, опишите вашу идею, предложение или отзыв одним сообщением.")
    await state.set_state(FeedbackState.waiting_for_feedback)

@router.message(FeedbackState.waiting_for_feedback)
async def feedback_received_handler(message: Message, state: FSMContext, bot):
    await log_event(message.from_user.id, 'feedback_submitted', message.text)
    
    # 1. Сохраняем в БД
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO feedback (user_id, feedback_text) VALUES ($1, $2)",
            message.from_user.id, message.text
        )
    
    # 2. Пересылаем админу
    await bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    
    # 3. Отвечаем пользователю
    await message.answer("Спасибо! Ваш отзыв получен и будет рассмотрен.")
    await state.clear()
