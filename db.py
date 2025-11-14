import asyncpg

from config import DATABASE_URL

DB_POOL: asyncpg.Pool | None = None


def get_connection_string() -> str:
    return DATABASE_URL


async def get_db_pool() -> asyncpg.Pool:
    global DB_POOL  # pylint: disable=global-statement
    if DB_POOL is None:
        DB_POOL = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)
    return DB_POOL
