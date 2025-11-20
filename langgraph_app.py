# langgraph_app.py
import asyncio
from typing import TypedDict, Annotated, Sequence, List
import operator
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Добавляем импорты из нашего проекта
from responses_client import (
    generate_rag_answer, generate_rag_digest, generate_rag_swot,
    generate_rag_nvc, generate_rag_po_helper, generate_rag_conflict
)
from assistant_client import run_assistant
from db import get_db_pool
from analytics import log_event
from formatters import markdown_to_html, format_citations, follow_up_markup
from kb_metadata import get_kb_structure
from admin_service import get_stats_text, get_feedback_text_and_keyboard, ADMIN_ID

CONFLICT_QUESTIONS = [
    "Опиши суть конфликта: кто вовлечён и в чём именно расхождения в целях или задачах.",
    "Какие позиции у каждого, что они считают важным и какую цель хотят защитить?",
    "Что ты наблюдаешь: какие эмоции и реакции проявляют участники?",
    "Какие потребности, ценности или предпосылки важны для каждой стороны?",
    "Что уже обсуждалось и какие попытки решения предпринимались?",
]

# 1. Определяем состояние графа
class AgentState(TypedDict):
    input_message: Message
    messages: Annotated[Sequence[BaseMessage], operator.add]
    command: str
    conflict_step: int
    conflict_answers: List[str]
    response: str
    response_titles: List[str]
    reply_markup: InlineKeyboardMarkup = None

# --- Карта соответствия команд и RAG/Assistant функций ---
RAG_COMMANDS = {
    "ask": generate_rag_answer, "digest": generate_rag_digest, "swot": generate_rag_swot,
    "nvc": generate_rag_nvc, "po_helper": generate_rag_po_helper,
}
ASSISTANT_COMMANDS = {
    "retro": "Сгенерируй подробный сценарий ретроспективы.",
    "icebreaker": "Придумай короткий icebreaker для IT-команды.",
}

# --- Узлы графа ---

async def route_command_node(state: AgentState) -> dict:
    """
    data_driven: Маршрутизирует команду, извлеченную из сообщения, на соответствующий узел графа.

    Использует словарь COMMAND_ROUTES для определения маршрута.
    """
    print("---ROUTE COMMAND---")
    message = state["input_message"]
    text = state["messages"][-1].content.lower()
    
    await log_event(message.from_user.id, text.split(' ')[0], text)

    COMMAND_ROUTES = {
        "/start": "assistant_tool",
        "/ask": "rag_ask",
        "/swot": "assistant_tool",
        "/nvc": "assistant_tool",
        "/po_helper": "assistant_tool",
        "/digest": "rag_digest",
        "/conflict": "conflict_resolution_start",
        "/kb": "kb_search_start",
        "/admin": "admin_main",
        "/feedback": "feedback_start",
        "/retro": "retrospective_start",
        "/icebreaker": "icebreaker_start",
    }

    command = text.split(' ')[0]
    
    if command in COMMAND_ROUTES:
        return {"command": COMMAND_ROUTES[command]}
    else:
        return {"command": "unknown"}

async def rag_node(state: AgentState):
    command = state["command"].replace("rag_", "")
    rag_function = RAG_COMMANDS[command]
    
    print(f"---RAG NODE: {command}---")
    query = state['messages'][-1].content.replace(f'/{command}', '').strip()
    if not query:
        return {"response": f"Пожалуйста, введите запрос, например: `/{command} [текст]`"}
    
    try:
        response_text, titles = await asyncio.get_running_loop().run_in_executor(None, rag_function, query)
        return {"response": response_text or "Не удалось...", "response_titles": titles, "reply_markup": follow_up_markup()}
    except Exception as e:
        print(f"Error in rag_node: {e}")
        return {"response": "К сожалению, произошла ошибка при обработке вашего запроса."}

async def assistant_node(state: AgentState):
    command = state["command"].replace("assistant_", "")
    prompt = ASSISTANT_COMMANDS[command]
    
    print(f"---ASSISTANT NODE: {command}---")
    
    try:
        response = await run_assistant([{"role": "user", "content": prompt}])
        return {"response": response.text, "response_titles": [c.file.name for c in response.citations if c.file], "reply_markup": follow_up_markup()}
    except Exception as e:
        print(f"Error in assistant_node: {e}")
        return {"response": "К сожалению, произошла ошибка при обращении к ассистенту."}

async def conflict_node(state: AgentState):
    print("---CONFLICT STEP---")
    step = state.get("conflict_step", 0)
    answers = state.get("conflict_answers", [])
    if step > 0: answers.append(state['messages'][-1].content)

    if step < len(CONFLICT_QUESTIONS):
        question = CONFLICT_QUESTIONS[step]
        return {"response": f"Вопрос {step + 1}/{len(CONFLICT_QUESTIONS)}: {question}", "conflict_step": step + 1, "conflict_answers": answers, "command": "conflict_in_progress"}
    
    print("---CONFLICT RESOLVE---")
    context = "\n".join(f"{i+1}. {ans}" for i, ans in enumerate(answers))
    response_text, _ = await asyncio.get_running_loop().run_in_executor(None, generate_rag_conflict, f"Контекст: {context}")
    return {"response": response_text or "Не удалось.", "conflict_step": 0, "conflict_answers": [], "command": ""}

async def kb_start_node(state: AgentState):
    print("---KB START---")
    categories = [c.name for c in await get_kb_structure()]
    if not categories: return {"response": "База знаний пуста."}
    
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"kb_cat_{name}")] for name in categories]
    return {"response": "<b>Тематики базы знаний:</b>", "reply_markup": InlineKeyboardMarkup(inline_keyboard=buttons), "command": "kb_browsing"}

async def kb_category_node(state: AgentState):
    print("---KB CATEGORY---")
    category_name = state['messages'][-1].content.replace('kb_cat_', '')
    topics = next((c.topics for c in await get_kb_structure() if c.name == category_name), [])
    
    if not topics: return {"response": "В этой категории нет тем."}
    
    text = f"<b>Тема: {category_name}</b>\n\n" + "\n".join([f"- {t}" for t in topics])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ К категориям", callback_data="kb_back_to_cats")]])
    return {"response": text, "reply_markup": keyboard, "command": "kb_browsing"}

async def admin_main_node(state: AgentState):
    print("---ADMIN MAIN---")
    if state['input_message'].from_user.id != ADMIN_ID: return {"response": "Доступ запрещен."}
    
    stats_text = await get_stats_text()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄", callback_data="admin_main"), InlineKeyboardButton(text="📝", callback_data="admin_feedback_0")]])
    return {"response": stats_text, "reply_markup": keyboard, "command": "admin_browsing"}

async def admin_feedback_node(state: AgentState):
    print("---ADMIN FEEDBACK---")
    if state['input_message'].from_user.id != ADMIN_ID: return {"response": "Доступ запрещен."}
    
    page = int(state['messages'][-1].content.split('_')[-1])
    text, keyboard = await get_feedback_text_and_keyboard(page)
    return {"response": text, "reply_markup": keyboard, "command": "admin_browsing"}

async def feedback_start_node(state: AgentState):
    print("---FEEDBACK START---")
    return {"response": "Пожалуйста, опишите вашу идею, предложение или отзыв одним сообщением.", "command": "feedback_in_progress"}

async def feedback_submit_node(state: AgentState):
    print("---FEEDBACK SUBMIT---")
    message = state['input_message']
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO feedback (user_id, feedback_text) VALUES ($1, $2)", message.from_user.id, message.text)
    
    await message.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    return {"response": "Спасибо! Ваш отзыв получен.", "command": ""}

async def unknown_command_node(state: AgentState):
    return {"response": "Неизвестная команда."}

async def response_node(state: AgentState):
    print("---RESPONSE---")
    response, message, reply_markup = state.get('response'), state.get('input_message'), state.get('reply_markup')
    
    if response and message:
        is_callback = state['messages'][-1].content.startswith(('kb_', 'admin_'))
        
        if is_callback:
            await message.edit_text(markdown_to_html(response), parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.answer(markdown_to_html(response), parse_mode="HTML", reply_markup=reply_markup)
        
        if titles := state.get('response_titles'):
            await message.answer(format_citations(titles), parse_mode="HTML", disable_web_page_preview=True)
    return {}

# 3. Собираем граф
def build_graph(checkpointer: MemorySaver):
    workflow = StateGraph(AgentState)
    
    nodes = {name: func for name, func in globals().items() if name.endswith('_node')}
    for name, node_func in nodes.items():
        if "rag_" in name or "assistant_" in name: continue
        workflow.add_node(name, node_func)

    workflow.add_node("rag", rag_node)
    workflow.add_node("assistant", assistant_node)
    workflow.set_entry_point("route_command")
    
    edges = ["unknown_command", "conflict", "kb_start", "kb_category", "admin_main", "admin_feedback", "rag", "assistant", "feedback_start", "feedback_submit"]
    for edge in edges:
        workflow.add_edge(edge, "response")

    rag_routes = {f"rag_{cmd}": "rag" for cmd in RAG_COMMANDS}
    assistant_routes = {f"assistant_{cmd}": "assistant" for cmd in ASSISTANT_COMMANDS}
    workflow.add_conditional_edges(
        "route_command",
        lambda x: x["command"],
        {**rag_routes, **assistant_routes, "conflict": "conflict", "kb_start": "kb_start", "kb_category": "kb_category", "admin_main": "admin_main", "admin_feedback": "admin_feedback", "feedback_start": "feedback_start", "feedback_submit": "feedback_submit", "unknown": "unknown_command"}
    )
    workflow.add_edge("response", END)

    return workflow.compile(checkpointer=checkpointer)