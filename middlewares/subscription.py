from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class SubscriptionState(StatesGroup):
    waiting_for_resubmission = State()
    original_command_type = State() # 'message' или 'callback'
    original_command_data = State() # текст команды или callback_data
    original_message_id = State()   # ID сообщения с запросом подписки

CHANNEL_ID = "@processoff"
CHANNEL_URL = "https://t.me/processoff"

class CheckSubscription(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot = data.get('bot')
        state: FSMContext = data.get('state')

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
            original_command_type = 'message'
            original_command_data = event.text
            message_to_delete_id = event.message_id # ID сообщения, которое будет удалено
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            original_command_type = 'callback'
            original_command_data = event.data
            message_to_delete_id = event.message.message_id # ID сообщения, которое будет удалено
        else:
            return await handler(event, data) # Пропускаем другие типы событий

        if user_id is None:
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status in ['creator', 'administrator', 'member']:
                return await handler(event, data)
        except Exception as e:
            print(f"Не удалось проверить подписку для пользователя {user_id}: {e}")
            # Если проверка не удалась (например, бот не админ), пропускаем пользователя
            return await handler(event, data)

        # Если пользователь не подписан, сохраняем его запрос и отправляем интерактивное сообщение
        await state.set_state(SubscriptionState.waiting_for_resubmission)
        await state.update_data(
            original_command_type=original_command_type,
            original_command_data=original_command_data,
            original_message_id=message_to_delete_id
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в канал", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="Я подписался ✅", callback_data="check_subscription")]
        ])

        await bot.send_message(
            chat_id=user_id,
            text="<b>Доступ для подписчиков</b>\n\nЭта функция доступна только подписчикам нашего канала.\n\n1. Нажмите на кнопку \"Перейти в канал\" и подпишитесь.\n2. Вернитесь в бот и нажмите \"Я подписался ✅\".",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        # Важно: не вызываем handler, чтобы заблокировать выполнение команды
        return
