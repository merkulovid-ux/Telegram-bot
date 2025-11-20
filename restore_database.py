"""
Скрипт для восстановления базы данных
Создает все необходимые таблицы и расширения
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from db import get_db_pool, DB_POOL
from config import DATABASE_URL
import os

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(message: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message: str):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message: str):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message: str):
    print(f"  {message}")

async def check_connection():
    """Проверка подключения к БД"""
    print_header("Проверка подключения к базе данных")
    
    # Если DATABASE_URL использует хост "db", заменяем на "localhost" для локального запуска
    db_url = DATABASE_URL
    if "db:5432" in db_url:
        db_url = db_url.replace("db:5432", "localhost:5432")
        print_info(f"Используется локальное подключение: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
    
    try:
        # Временно изменяем DATABASE_URL для подключения
        import asyncpg
        pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT version()")
                print_success("Подключение к базе данных установлено")
                print_info(f"PostgreSQL версия: {result.split(',')[0]}")
        finally:
            await pool.close()
        return True
    except Exception as e:
        print_error(f"Не удалось подключиться к базе данных: {e}")
        print_info("Убедитесь, что:")
        print_info("  1. Docker контейнер с БД запущен (docker-compose up -d db)")
        print_info("  2. DATABASE_URL в .env файле корректный")
        print_info("  3. БД доступна на localhost:5432")
        return False

def get_local_db_url():
    """Получить URL БД для локального подключения"""
    db_url = DATABASE_URL
    if "db:5432" in db_url:
        db_url = db_url.replace("db:5432", "localhost:5432")
    return db_url

async def create_extension():
    """Создание расширения vector"""
    print_header("Создание расширения vector")
    
    try:
        import asyncpg
        db_url = get_local_db_url()
        pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
        try:
            async with pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print_success("Расширение vector создано/проверено")
        finally:
            await pool.close()
        return True
    except Exception as e:
        print_error(f"Ошибка при создании расширения vector: {e}")
        return False

async def create_tables():
    """Создание всех необходимых таблиц"""
    print_header("Создание таблиц")
    
    tables_sql = {
        "documents": """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                source TEXT,
                loc TEXT,
                content TEXT,
                embedding vector(256)
            );
        """,
        "events": """
            DROP TABLE IF EXISTS events;
            CREATE TABLE events (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                command TEXT,
                full_text TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        """,
        "knowledge_base_topics": """
            CREATE TABLE IF NOT EXISTS knowledge_base_topics (
                id SERIAL PRIMARY KEY,
                category TEXT,
                topic TEXT
            );
        """,
        "feedback": """
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                feedback_text TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        """
    }
    
    import asyncpg
    db_url = get_local_db_url()
    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
    try:
        async with pool.acquire() as conn:
            for table_name, sql in tables_sql.items():
                try:
                    await conn.execute(sql)
                    print_success(f"Таблица {table_name} создана/проверена")
                except Exception as e:
                    print_error(f"Ошибка при создании таблицы {table_name}: {e}")
                    return False
    finally:
        await pool.close()
    return True

async def create_indexes():
    """Создание индексов для оптимизации"""
    print_header("Создание индексов")
    
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);",
        "CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_topics_category ON knowledge_base_topics(category);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);",
        # Индекс для векторного поиска (используется оператором <=>)
        "CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    ]
    
    import asyncpg
    db_url = get_local_db_url()
    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
    try:
        async with pool.acquire() as conn:
            for sql in indexes_sql:
                try:
                    await conn.execute(sql)
                    print_info(f"Индекс создан/проверен")
                except Exception as e:
                    # Индекс для векторов может не создаться, если нет данных
                    if "ivfflat" in sql.lower():
                        print_info(f"  Предупреждение: векторный индекс не создан (возможно, нет данных): {e}")
                    else:
                        print_error(f"Ошибка при создании индекса: {e}")
    finally:
        await pool.close()
    return True

async def verify_tables():
    """Проверка, что все таблицы созданы"""
    print_header("Проверка структуры базы данных")
    
    expected_tables = ["documents", "events", "knowledge_base_topics", "feedback"]
    
    import asyncpg
    db_url = get_local_db_url()
    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
    try:
        async with pool.acquire() as conn:
            for table_name in expected_tables:
                try:
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = $1",
                        table_name
                    )
                    if count > 0:
                        # Получаем количество строк
                        row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                        print_success(f"Таблица {table_name} существует ({row_count} строк)")
                    else:
                        print_error(f"Таблица {table_name} не найдена")
                        return False
                except Exception as e:
                    print_error(f"Ошибка при проверке таблицы {table_name}: {e}")
                    return False
    finally:
        await pool.close()
    return True

async def check_vector_extension():
    """Проверка расширения vector"""
    print_header("Проверка расширения vector")
    
    try:
        import asyncpg
        db_url = get_local_db_url()
        pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if result:
                    print_success("Расширение vector установлено")
                    return True
                else:
                    print_error("Расширение vector не установлено")
                    return False
        finally:
            await pool.close()
    except Exception as e:
        print_error(f"Ошибка при проверке расширения vector: {e}")
        return False

async def show_statistics():
    """Показать статистику по таблицам"""
    print_header("Статистика базы данных")
    
    import asyncpg
    db_url = get_local_db_url()
    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
    try:
        async with pool.acquire() as conn:
            tables = ["documents", "events", "knowledge_base_topics", "feedback"]
            
            for table_name in tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    print_info(f"{table_name}: {count} записей")
                except Exception as e:
                    print_error(f"Ошибка при получении статистики для {table_name}: {e}")
    finally:
        await pool.close()

async def restore_database():
    """Основная функция восстановления БД"""
    print(f"\n{BLUE}{'#'*60}{RESET}")
    print(f"{BLUE}#  Восстановление базы данных{RESET}")
    print(f"{BLUE}{'#'*60}{RESET}")
    
    # Проверка подключения
    if not await check_connection():
        return False
    
    # Создание расширения
    if not await create_extension():
        return False
    
    # Создание таблиц
    if not await create_tables():
        return False
    
    # Создание индексов
    await create_indexes()
    
    # Проверка структуры
    if not await verify_tables():
        return False
    
    # Проверка расширения
    if not await check_vector_extension():
        return False
    
    # Статистика
    await show_statistics()
    
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}✓ База данных успешно восстановлена!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}")
    
    print_info("\nСледующие шаги:")
    print_info("  1. Запустите ingest.py для загрузки документов в БД")
    print_info("  2. Проверьте подключение бота к БД")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(restore_database())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Прервано пользователем{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Закрываем пулы соединений
        pass
