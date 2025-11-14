from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext

from analytics import log_event
from kb_metadata import get_kb_structure
from states import KbState

router = Router()


def _render_categories_page(categories: list[str]) -> tuple[str, InlineKeyboardMarkup | None]:
    if not categories:
        return "База знаний пока пуста. Загрузите документы и повторите команду /kb.", None

    buttons = [
        InlineKeyboardButton(text=category, callback_data=f"kb_cat_{idx}")
        for idx, category in enumerate(categories)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button] for button in buttons])
    text = (
        "<b>Тематики базы знаний</b>\n\n"
        "Нажмите на тему, чтобы увидеть описание. Затем используйте /ask <вопрос>, и я подберу ответ на основе этой категории.\n"
        "Категория <b>Coaching</b> объединяет медиативные сценарии для Scrum Master, Agile Coach и фасилитатора, а разделы «Общее» и «Scrum» сопровождаются подсказками, какие роли ведут обсуждение. "
        "Для подробностей о ролях и компетенциях смотрите `TEAM.md` (Scrum Master, Product Owner, Coach)."
    )
    return text, keyboard


def _render_topics_page(category: str, page: int, topics: list[str]) -> tuple[str, InlineKeyboardMarkup | None]:
    text = (
        f"<b>Тема: {category}</b>\n\n"
        "Это описание выбранной темы. Чтобы задать вопросы по ней, отправьте:\n"
        "<code>/ask <ваш вопрос по теме></code>\n"
        "Ответ будет сформирован на основе документов из этой категории."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ К категориям", callback_data="kb_back_to_cats")]
        ]
    )
    return text, keyboard


@router.message(Command("kb"))
async def knowledge_base_entry_handler(message: Message, state: FSMContext):
    await log_event(message.from_user.id, "/kb", message.text)

    categories_data = await get_kb_structure()
    category_names = [c.name for c in categories_data]
    topics_map = {c.name: c.topics for c in categories_data}

    text, keyboard = _render_categories_page(category_names)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(KbState.browsing_categories)
    await state.update_data(kb_categories=category_names, kb_topics=topics_map)


async def _ensure_state_categories(state: FSMContext):
    data = await state.get_data()
    category_names = data.get("kb_categories")
    topics_map = data.get("kb_topics")
    if category_names and topics_map:
        return category_names, topics_map

    categories_data = await get_kb_structure(force_refresh=True)
    category_names = [c.name for c in categories_data]
    topics_map = {c.name: c.topics for c in categories_data}
    await state.update_data(kb_categories=category_names, kb_topics=topics_map)
    return category_names, topics_map


@router.callback_query(KbState.browsing_categories, F.data.startswith("kb_cat_"))
async def category_selected_handler(callback_query: CallbackQuery, state: FSMContext):
    cat_index = int(callback_query.data.split("_")[2])
    category_names, topics_map = await _ensure_state_categories(state)

    try:
        category = category_names[cat_index]
    except (IndexError, TypeError):
        await callback_query.answer("Категория не найдена. Попробуйте снова через /kb.", show_alert=True)
        return

    await log_event(callback_query.from_user.id, "kb_category_selected", category)
    text, keyboard = _render_topics_page(category, 0, topics_map.get(category, []))

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(KbState.browsing_topics)
    await state.update_data(current_category=category)
    await callback_query.answer()


@router.callback_query(KbState.browsing_topics, F.data.startswith("kb_topics_"))
async def topics_pagination_handler(callback_query: CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split("_")[2])
    data = await state.get_data()
    category = data.get("current_category")
    topics_map = data.get("kb_topics")

    if not category:
        await callback_query.answer(
            "Категория потеряна. Начните заново с /kb.", show_alert=True
        )
        return
    if not topics_map:
        _, topics_map = await _ensure_state_categories(state)

    await log_event(callback_query.from_user.id, "kb_topics_pagination", f"{category}_page_{page}")
    text, keyboard = _render_topics_page(category, page, topics_map.get(category, []))

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "kb_back_to_cats")
async def back_to_categories_handler(callback_query: CallbackQuery, state: FSMContext):
    await log_event(callback_query.from_user.id, "kb_back_to_categories", "")
    category_names, _ = await _ensure_state_categories(state)
    text, keyboard = _render_categories_page(category_names)

    await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(KbState.browsing_categories)
    await callback_query.answer()
