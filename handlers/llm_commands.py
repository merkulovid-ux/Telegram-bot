from __future__ import annotations

import asyncio
import html
import re
import logging
from typing import Awaitable, Callable, Dict, Iterable

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from analytics import log_event
from assistant_client import format_citations, run_assistant
from responses_client import (
    generate_rag_answer,
    generate_rag_conflict,
    generate_rag_swot,
    generate_rag_digest,
    generate_rag_nvc,
    generate_rag_po_helper,
)
from states import Conversation, Form

router = Router()

logger = logging.getLogger(__name__)

CommandProcessor = Callable[[Message, str, FSMContext], Awaitable[None]]
COMMAND_PROCESSORS: Dict[str, tuple[str, CommandProcessor]]

DEFAULT_FALLBACK = "Извините, не удалось получить ответ. Попробуйте позже."


def _markdown_to_html(raw: str) -> str:
    safe = html.escape(raw.strip()) or DEFAULT_FALLBACK
    safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
    safe = re.sub(r'(?m)^(\*|-)\s+(.*)', "\u2022 \\2", safe)
    safe = re.sub(r'(?m)^#{1,6}\s+(.*)', r'<b>\1</b>', safe)
    return safe


def _follow_up_markup() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ещё")],
            [KeyboardButton(text="Уточнить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

async def _call_assistant(
    messages: Iterable[dict[str, str]],
    message: Message,
    *,
    fallback: str = DEFAULT_FALLBACK,
    thread_id: str | None = None,
    reply_markup: ReplyKeyboardMarkup | ReplyKeyboardRemove | None = None,
):
    try:
        response = await run_assistant(messages, thread_id=thread_id)
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"Произошла ошибка при работе с ассистентом: {exc}")
        return None

    text = (response.text or "").strip() or fallback
    await message.answer(_markdown_to_html(text), parse_mode="HTML", reply_markup=reply_markup)

    citation_text = format_citations(response.citations)
    if citation_text:
        await message.answer(citation_text, disable_web_page_preview=True)

    return response


async def process_ask(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    # Stateless RAG через Responses API (без ассистентов/threads)
    text, titles = await asyncio.get_running_loop().run_in_executor(None, generate_rag_answer, query)
    text = text or "Не удалось сформировать ответ. Попробуйте переформулировать запрос."
    await message.answer(text)
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/ask", assistant_thread_id="")


async def process_digest(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    logger.info("process_digest via stateless RAG")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_digest, query)
    text = text or "�� ������� ������� �������� �� �������, ���������� ����������������� ����."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await message.answer(
        "������� ����� ��� ����������, ���� ������ ����������, � � ������� ����� ����.",
        parse_mode="HTML",
        reply_markup=_follow_up_markup(),
    )
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/digest", assistant_thread_id="")

async def process_nvc(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_nvc, query)
    text = text or "Не удалось переписать фразу. Попробуйте уточнить."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/nvc", assistant_thread_id="")


async def process_po_helper(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_po_helper, query)
    text = text or "Не удалось сформулировать совет. Попробуйте уточнить запрос."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/po_helper", assistant_thread_id="")


async def process_swot(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, titles = await asyncio.get_running_loop().run_in_executor(None, generate_rag_swot, query)
    text = text or "Не удалось сформировать SWOT-ответ. Попробуйте сузить запрос."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/swot", assistant_thread_id="")


CONFLICT_QUESTIONS = [
    "Опиши суть конфликта: кто вовлечён и в чём именно расхождения в целях или задачах.",
    "Какие позиции у каждого, что они считают важным и какую цель хотят защитить?",
    "Что ты наблюдаешь: какие эмоции и реакции проявляют участники?",
    "Какие потребности, ценности или предпосылки важны для каждой стороны?",
    "Что уже обсуждалось и какие попытки решения предпринимались?",
]


async def _ask_conflict_question(message: Message, step: int):
    question = CONFLICT_QUESTIONS[step]
    await message.answer(f"Вопрос {step + 1}/{len(CONFLICT_QUESTIONS)}: {question}")


async def process_conflict(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    data = await state.get_data()
    step = data.get("conflict_step", 0)
    answers = data.get("conflict_answers", [])

    if not query:
        await message.answer(
            "����������, � ��� ��������: ��� ���������, ���� ����� ������ � � ��� �������� ����������."
        )
        await state.set_state(Form.waiting_for_argument)
        await state.update_data(
            processor="conflict", pending_command="conflict", conflict_step=0, conflict_answers=[]
        )
        return

    answers.append(query)
    if step < len(CONFLICT_QUESTIONS):
        await _ask_conflict_question(message, step)
        await state.set_state(Form.waiting_for_argument)
        await state.update_data(
            processor="conflict",
            pending_command="conflict",
            conflict_step=step + 1,
            conflict_answers=answers,
        )
        return

    context = "
".join(f"{i+1}. {ans}" for i, ans in enumerate(answers))
    text, _ = await asyncio.get_running_loop().run_in_executor(
        None, generate_rag_conflict, f"{query}

�������:
{context}"
    )
    text = text or "��� ������� ���� ������ ������� ����������� ��������. ���������� �������� �������."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await message.answer(
        "������� ����� ��� ����������, ���� ������ ���������� ����������� ������ ��� ������ ���������� �������.",
        parse_mode="HTML",
        reply_markup=_follow_up_markup(),
    )
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/conflict", assistant_thread_id="")

COMMAND_PROCESSORS: Dict[str, tuple[str, CommandProcessor]]

DEFAULT_FALLBACK = "Извините, не удалось получить ответ. Попробуйте позже."


def _markdown_to_html(raw: str) -> str:
    safe = html.escape(raw.strip()) or DEFAULT_FALLBACK
    safe = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)
    safe = re.sub(r'(?m)^(\*|-)\s+(.*)', "\u2022 \\2", safe)
    safe = re.sub(r'(?m)^#{1,6}\s+(.*)', r'<b>\1</b>', safe)
    return safe


def _follow_up_markup() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ещё")],
            [KeyboardButton(text="Уточнить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

async def _call_assistant(
    messages: Iterable[dict[str, str]],
    message: Message,
    *,
    fallback: str = DEFAULT_FALLBACK,
    thread_id: str | None = None,
    reply_markup: ReplyKeyboardMarkup | ReplyKeyboardRemove | None = None,
):
    try:
        response = await run_assistant(messages, thread_id=thread_id)
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"Произошла ошибка при работе с ассистентом: {exc}")
        return None

    text = (response.text or "").strip() or fallback
    await message.answer(_markdown_to_html(text), parse_mode="HTML", reply_markup=reply_markup)

    citation_text = format_citations(response.citations)
    if citation_text:
        await message.answer(citation_text, disable_web_page_preview=True)

    return response


async def process_ask(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    # Stateless RAG через Responses API (без ассистентов/threads)
    text, titles = await asyncio.get_running_loop().run_in_executor(None, generate_rag_answer, query)
    text = text or "Не удалось сформировать ответ. Попробуйте переформулировать запрос."
    await message.answer(text)
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/ask", assistant_thread_id="")


async def process_digest(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    logger.info("process_digest via stateless RAG")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_digest, query)
    text = text or "�� ������� ������� �������� �� �������, ���������� ����������������� ����."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await message.answer(
        "������� ����� ��� ����������, ���� ������ ����������, � � ������� ����� ����.",
        parse_mode="HTML",
        reply_markup=_follow_up_markup(),
    )
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/digest", assistant_thread_id="")

async def process_nvc(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_nvc, query)
    text = text or "Не удалось переписать фразу. Попробуйте уточнить."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/nvc", assistant_thread_id="")


async def process_po_helper(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_po_helper, query)
    text = text or "Не удалось сформулировать совет. Попробуйте уточнить запрос."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/po_helper", assistant_thread_id="")


async def process_swot(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    text, titles = await asyncio.get_running_loop().run_in_executor(None, generate_rag_swot, query)
    text = text or "Не удалось сформировать SWOT-ответ. Попробуйте сузить запрос."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/swot", assistant_thread_id="")


CONFLICT_QUESTIONS = [
    "Опиши суть конфликта: кто вовлечён и в чём именно расхождения в целях или задачах.",
    "Какие позиции у каждого, что они считают важным и какую цель хотят защитить?",
    "Что ты наблюдаешь: какие эмоции и реакции проявляют участники?",
    "Какие потребности, ценности или предпосылки важны для каждой стороны?",
    "Что уже обсуждалось и какие попытки решения предпринимались?",
]


async def _ask_conflict_question(message: Message, step: int):
    question = CONFLICT_QUESTIONS[step]
    await message.answer(f"Вопрос {step + 1}/{len(CONFLICT_QUESTIONS)}: {question}")


async def process_conflict(message: Message, query: str, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    data = await state.get_data()
    step = data.get("conflict_step", 0)
    answers = data.get("conflict_answers", [])

    if not query:
        await message.answer(
            "Опиши ситуацию: кто вовлечён, о чём разногласия и какие симптомы конфликта ты наблюдаешь."
        )
        await state.set_state(Form.waiting_for_argument)
        await state.update_data(
            processor="conflict", pending_command="conflict", conflict_step=0, conflict_answers=[]
        )
        return

    answers.append(query)
    if step < len(CONFLICT_QUESTIONS):
        await _ask_conflict_question(message, step)
        await state.set_state(Form.waiting_for_argument)
        await state.update_data(
            processor="conflict",
            pending_command="conflict",
            conflict_step=step + 1,
            conflict_answers=answers,
        )
        return

    context = "\n".join(f"{i+1}. {ans}" for i, ans in enumerate(answers))
    text, _ = await asyncio.get_running_loop().run_in_executor(
        None, generate_rag_conflict, f"{query}\n\nИстория:\n{context}"
    )
    text = text or "Не удалось сформировать медиативное предложение. Попробуй уточнить детали."
    await message.answer(_markdown_to_html(text), parse_mode="HTML")
    await message.answer(
        "Если нужно уточнить контекст или позиции — ответь «да» или напиши дополнительный вопрос.",
        parse_mode="HTML",
    )
    await state.set_state(Conversation.waiting_for_follow_up)
    await state.update_data(original_query=query, source_command="/conflict", assistant_thread_id="")


COMMAND_PROCESSORS = {
    "ask": ("Расскажи, что именно нужно узнать.", process_ask),
    "digest": ("Напиши тему, по которой нужен дайджест.", process_digest),
    "nvc": ("Напиши фразу, которую нужно переформулировать в ННО.", process_nvc),
    "po_helper": ("Выслушаю запрос Product Owner: уточни задачу.", process_po_helper),
    "swot": ("Опиши объект/компанию для SWOT-анализа.", process_swot),
    "conflict": ("Опиши конфликтную ситуацию, которую нужно медиировать.", process_conflict),
}


async def command_parser_handler(message: Message, state: FSMContext, command: str):
    await log_event(message.from_user.id, f"/{command}", message.text)
    normalized = command.lower()
    query = message.text.replace(f"/{command}", "", 1).strip()
    prompt_text, processor_func = COMMAND_PROCESSORS.get(normalized, ("", None))

    if not processor_func:
        await message.answer("Неизвестная команда. Попробуйте /ask, /digest и т.п.")
        return

    if query:
        await processor_func(message, query, state)
    else:
        await message.answer(prompt_text)
        await state.set_state(Form.waiting_for_argument)
        await state.update_data(processor=normalized, pending_command=normalized)


@router.message(Command("ask"))
async def ask_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "ask")


@router.message(Command("digest"))
async def digest_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "digest")


@router.message(Command("nvc"))
async def nvc_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "nvc")


@router.message(Command("po_helper"))
async def po_helper_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "po_helper")


@router.message(Command("swot"))
async def swot_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "swot")


@router.message(Command("conflict"))
async def conflict_handler(message: Message, state: FSMContext):
    await command_parser_handler(message, state, "conflict")


@router.message(Form.waiting_for_argument)
async def argument_provided_handler(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    command = data.get("processor") or data.get("pending_command")
    query = message.text.strip()

    if command in COMMAND_PROCESSORS:
        _, processor_func = COMMAND_PROCESSORS[command]
        await processor_func(message, query, state)
        await state.clear()
    else:
        await state.clear()
        await message.answer("Произошла ошибка. Попробуйте начать заново.")


async def retro_template(message: Message, prompt: str, fallback: str):
    await _call_assistant(
        [
            {
                "role": "system",
                "content": (
                    "Ты — AI-помощник, который помогает сгенерировать сценарии ретроспектив "
                    "и командные активности. Будь структурированным и вдохновляющим."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        message,
        fallback=fallback,
    )


@router.message(Command("retro"))
async def retro_command_handler(message: Message, bot):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await log_event(message.from_user.id, "/retro", message.text)
    await retro_template(
        message,
        "Сгенерируй подробный сценарий ретроспективы.",
        "Извините, не удалось придумать сценарий. Попробуйте позже.",
    )


@router.message(Command("icebreaker"))
async def icebreaker_command_handler(message: Message, bot):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await log_event(message.from_user.id, "/icebreaker", message.text)
    await retro_template(
        message,
        "Придумай короткий icebreaker для IT-команды.",
        "Извините, не удалось сгенерировать icebreaker. Попробуйте позже.",
    )


@router.message(Conversation.waiting_for_follow_up)
async def handle_follow_up(message: Message, state: FSMContext, bot):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    user_input = message.text.lower().strip()

    yes_variants = {"��", "�������", "�����", "���", "yes", "��", "���", "���", "��������", "��������"}
    if user_input not in yes_variants:
        await message.answer("Хорошо! Если появится новый вопрос, просто напиши /ask или выбери команду из меню.")
        await state.clear()
        return

    data = await state.get_data()
    original_query = data.get("original_query")
    thread_id = data.get("assistant_thread_id")

    if not thread_id:
        await message.answer("Не удалось найти предыдущий диалог. Попробуй задать вопрос заново.")
        await state.clear()
        return

    follow_up_prompt = (
        f"Пользователь хочет продолжить обсуждать тему: {original_query}. "
        "Продолжи ответ, добавь больше деталей и советов."
    )
    response = await _call_assistant(
        [{"role": "user", "content": follow_up_prompt}],
        message,
        thread_id=thread_id,
        reply_markup=ReplyKeyboardRemove(),
    )
    if response:
        await state.update_data(assistant_thread_id=response.thread_id)

    await state.clear()
