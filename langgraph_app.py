import asyncio
from typing import Annotated, Dict, List, Sequence, TypedDict
import operator

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from responses_client import (
    generate_rag_answer,
    generate_rag_conflict,
    generate_rag_digest,
    generate_rag_nvc,
    generate_rag_po_helper,
    generate_rag_swot,
)
from assistant_client import run_assistant
from db import get_db_pool
from analytics import log_event
from formatters import markdown_to_html, format_citations, follow_up_markup
from kb_metadata import get_kb_structure
from admin_service import get_stats_text, get_feedback_text_and_keyboard, ADMIN_ID

CONFLICT_QUESTIONS = [
    "Опишите конфликтную ситуацию и участников.",
    "Что уже предпринималось для решения?",
    "Какой результат вы считаете успешным?",
    "Есть ли ограничения/сроки?",
    "Что нужно учесть, чтобы решение было устойчивым?",
]


class AgentState(TypedDict):
    input_message: Message
    messages: Annotated[Sequence[BaseMessage], operator.add]
    command: str
    conflict_step: int
    conflict_answers: List[str]
    response: str
    response_titles: List[str]
    reply_markup: InlineKeyboardMarkup | None


RAG_COMMANDS = {
    "ask": generate_rag_answer,
    "digest": generate_rag_digest,
    "swot": generate_rag_swot,
    "nvc": generate_rag_nvc,
    "po_helper": generate_rag_po_helper,
}

ASSISTANT_COMMANDS = {
    "retro": "Подготовь чек-лист для ретро команды разработки.",
    "icebreaker": "Дай 3 идеи icebreaker для ИТ-команды.",
}


async def start_node(state: AgentState):
    return {"response": "Привет! Я ProcessOff Bot для Cloud.ru.\n\nДоступные команды:\n/ask <вопрос> - поиск по базе знаний\n/kb - структура базы знаний\n/digest <тема> - саммари темы\n/swot <тема> - SWOT-анализ\n/retro, /icebreaker - сценарии для встреч\n/feedback - отправить отзыв", "command": ""}

async def route_command_node(state: AgentState) -> dict:
    message = state["input_message"]
    text = state["messages"][-1].content.lower()
    try:
        await log_event(message.from_user.id, text.split(" ")[0], text)
    except Exception:
        pass

    routes = {
        "/start": "start_cmd",
        "/ask": "rag_ask",
        "/digest": "rag_digest",
        "/swot": "rag_swot",
        "/nvc": "rag_nvc",
        "/po_helper": "rag_po_helper",
        "/conflict": "conflict_resolution_start",
        "/kb": "kb_search_start",
        "/admin": "admin_main",
        "/feedback": "feedback_start",
        "/retro": "assistant_retro",
        "/icebreaker": "assistant_icebreaker",
    }
    command = text.split(" ")[0]
    return {"command": routes.get(command, "unknown")}


async def rag_node(state: AgentState):
    command = state["command"].replace("rag_", "")
    rag_function = RAG_COMMANDS[command]
    query = state["messages"][-1].content.replace(f"/{command}", "").strip()
    if not query:
        return {"response": f"Уточните запрос: `/{command} [тема]`"}
    response_text, titles = await rag_function(query)
    return {"response": response_text or "Нет ответа.", "response_titles": titles, "reply_markup": follow_up_markup()}


async def assistant_node(state: AgentState):
    command = state["command"].replace("assistant_", "")
    prompt = ASSISTANT_COMMANDS[command]
    response = await run_assistant([{"role": "user", "content": prompt}])
    return {"response": response.text, "response_titles": list(response.citations), "reply_markup": follow_up_markup()}


async def conflict_node(state: AgentState):
    step = state.get("conflict_step", 0)
    answers = state.get("conflict_answers", [])
    if step > 0:
        answers.append(state["messages"][-1].content)

    if step < len(CONFLICT_QUESTIONS):
        question = CONFLICT_QUESTIONS[step]
        return {
            "response": f"Вопрос {step + 1}/{len(CONFLICT_QUESTIONS)}: {question}",
            "conflict_step": step + 1,
            "conflict_answers": answers,
            "command": "conflict_in_progress",
        }

    context = "\n".join(f"{i+1}. {ans}" for i, ans in enumerate(answers))
    response_text, _ = await generate_rag_conflict(f"Контекст конфликта: {context}")
    return {"response": response_text or "Нет ответа.", "conflict_step": 0, "conflict_answers": [], "command": ""}


async def kb_start_node(state: AgentState):
    categories = [c.name for c in await get_kb_structure()]
    if not categories:
        return {"response": "База знаний пуста."}
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"kb_cat_{name}")] for name in categories]
    return {"response": "<b>Категории базы знаний:</b>", "reply_markup": InlineKeyboardMarkup(inline_keyboard=buttons), "command": "kb_browsing"}


async def kb_category_node(state: AgentState):
    category_name = state["messages"][-1].content.replace("kb_cat_", "")
    topics = next((c.topics for c in await get_kb_structure() if c.name == category_name), [])
    if not topics:
        return {"response": "Темы не найдены."}
    text = f"<b>Темы: {category_name}</b>\n\n" + "\n".join([f"- {t}" for t in topics])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="kb_back_to_cats")]])
    return {"response": text, "reply_markup": keyboard, "command": "kb_browsing"}


async def admin_main_node(state: AgentState):
    if state["input_message"].from_user.id != ADMIN_ID:
        return {"response": "Нет доступа."}
    stats_text = await get_stats_text()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отчеты", callback_data="admin_main"), InlineKeyboardButton(text="Фидбек", callback_data="admin_feedback_0")]])
    return {"response": stats_text, "reply_markup": keyboard, "command": "admin_browsing"}


async def admin_feedback_node(state: AgentState):
    if state["input_message"].from_user.id != ADMIN_ID:
        return {"response": "Нет доступа."}
    page = int(state["messages"][-1].content.split("_")[-1])
    text, keyboard = await get_feedback_text_and_keyboard(page)
    return {"response": text, "reply_markup": keyboard, "command": "admin_browsing"}


async def feedback_start_node(state: AgentState):
    return {"response": "Опишите ваш отзыв одним сообщением — мы передадим администратору.", "command": "feedback_in_progress"}


async def feedback_submit_node(state: AgentState):
    message = state["input_message"]
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO feedback (user_id, feedback_text) VALUES ($1, $2)", message.from_user.id, message.text)
        await message.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        return {"response": "Спасибо! Отзыв передан.", "command": ""}
    except Exception:
        return {"response": "Не удалось сохранить отзыв, попробуйте позже.", "command": ""}


async def unknown_command_node(state: AgentState):
    return {"response": "Неизвестная команда."}


async def response_node(state: AgentState):
    response, message, reply_markup = state.get("response"), state.get("input_message"), state.get("reply_markup")
    if response and message:
        is_callback = state["messages"][-1].content.startswith(("kb_", "admin_"))
        if is_callback:
            await message.edit_text(markdown_to_html(response), parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.answer(markdown_to_html(response), parse_mode="HTML", reply_markup=reply_markup)
        if titles := state.get("response_titles"):
            await message.answer(format_citations(titles), parse_mode="HTML", disable_web_page_preview=True)
    return {}


def build_graph(checkpointer: MemorySaver):
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("start", start_node)
    workflow.add_node("route_command", route_command_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("assistant", assistant_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("kb_start", kb_start_node)
    workflow.add_node("kb_category", kb_category_node)
    workflow.add_node("admin_main", admin_main_node)
    workflow.add_node("admin_feedback", admin_feedback_node)
    workflow.add_node("feedback_start", feedback_start_node)
    workflow.add_node("feedback_submit", feedback_submit_node)
    workflow.add_node("unknown_command", unknown_command_node)
    workflow.add_node("response", response_node)

    workflow.set_entry_point("route_command")

    rag_routes = {f"rag_{cmd}": "rag" for cmd in RAG_COMMANDS}
    assistant_routes = {f"assistant_{cmd}": "assistant" for cmd in ASSISTANT_COMMANDS}
    workflow.add_conditional_edges(
        "route_command",
        lambda x: x["command"],
        {
            **rag_routes,
            **assistant_routes,
            "start_cmd": "start",
            "conflict": "conflict",
            "kb_start": "kb_start",
            "kb_category": "kb_category",
            "admin_main": "admin_main",
            "admin_feedback": "admin_feedback",
            "feedback_start": "feedback_start",
            "feedback_submit": "feedback_submit",
            "unknown": "unknown_command",
        },
    )

    for edge in ["unknown_command", "start", "conflict", "kb_start", "kb_category", "admin_main", "admin_feedback", "rag", "assistant", "feedback_start", "feedback_submit"]:
        workflow.add_edge(edge, "response")

    workflow.add_edge("response", END)
    return workflow.compile(checkpointer=checkpointer)
