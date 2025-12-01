import logging
from db import get_db_pool

logger = logging.getLogger(__name__)

async def log_event(user_id: int, command: str, full_text: str = None):
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO events (user_id, command, full_text)
                   VALUES ($1, $2, $3)""",
                user_id, command, full_text
            )
    except Exception as exc:
        # best-effort: не блокируем диалог, если БД временно недоступна
        logger.warning("log_event skipped due to DB error: %s", exc)
