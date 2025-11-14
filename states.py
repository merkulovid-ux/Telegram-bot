from aiogram.fsm.state import State, StatesGroup

# Состояние для ожидания ответа "да/нет" на предложение продолжить
class Conversation(StatesGroup):
    waiting_for_follow_up = State()

# Состояние для ожидания недостающего аргумента для команды
class Form(StatesGroup):
    waiting_for_argument = State()

# Состояния для навигации по базе знаний
class KbState(StatesGroup):
    browsing_categories = State()
    browsing_topics = State()