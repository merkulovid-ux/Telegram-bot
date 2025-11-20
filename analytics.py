from db import get_db_pool

async def log_event(user_id: int, command: str, full_text: str = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO events (user_id, command, full_text)
               VALUES ($1, $2, $3)""",
            user_id, command, full_text
        )
