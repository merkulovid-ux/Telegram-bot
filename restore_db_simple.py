"""
Простой скрипт для восстановления базы данных
Использует прямое подключение через psycopg2
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL не установлен в .env файле")
    sys.exit(1)

# Заменяем db на localhost для локального подключения
if "db:5432" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:5432")

print("🔧 Восстановление базы данных...")
print(f"📡 Подключение к: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

try:
    # Парсим URL
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port or 5432,
        user=result.username,
        password=result.password,
        dbname=result.path[1:] if result.path else 'ai_bot',
        client_encoding='UTF8'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    print("✅ Подключение установлено")
    
    # 1. Создание расширения vector
    print("\n📦 Создание расширения vector...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("✅ Расширение vector создано")
    
    # 2. Создание таблиц
    print("\n📊 Создание таблиц...")
    
    # Таблица documents
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            source TEXT,
            loc TEXT,
            content TEXT,
            embedding vector(256)
        );
    """)
    print("✅ Таблица documents создана")
    
    # Таблица events (DROP IF EXISTS для пересоздания)
    cur.execute("DROP TABLE IF EXISTS events;")
    cur.execute("""
        CREATE TABLE events (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            command TEXT,
            full_text TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    print("✅ Таблица events создана")
    
    # Таблица knowledge_base_topics
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base_topics (
            id SERIAL PRIMARY KEY,
            category TEXT,
            topic TEXT
        );
    """)
    print("✅ Таблица knowledge_base_topics создана")
    
    # Таблица feedback
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            feedback_text TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    print("✅ Таблица feedback создана")
    
    # 3. Создание индексов
    print("\n🔍 Создание индексов...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);",
        "CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_topics_category ON knowledge_base_topics(category);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);",
    ]
    
    for idx_sql in indexes:
        try:
            cur.execute(idx_sql)
            print(f"✅ Индекс создан")
        except Exception as e:
            print(f"⚠️  Предупреждение при создании индекса: {e}")
    
    # Векторный индекс (может не создаться, если нет данных)
    try:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_embedding 
            ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """)
        print("✅ Векторный индекс создан")
    except Exception as e:
        print(f"⚠️  Векторный индекс не создан (нормально, если нет данных): {e}")
    
    # 4. Проверка структуры
    print("\n🔍 Проверка структуры...")
    
    tables = ["documents", "events", "knowledge_base_topics", "feedback"]
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"✅ Таблица {table}: {count} записей")
    
    # 5. Проверка расширения
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
    if cur.fetchone()[0]:
        print("✅ Расширение vector установлено")
    else:
        print("❌ Расширение vector не установлено")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ База данных успешно восстановлена!")
    print("="*60)
    print("\n📝 Следующие шаги:")
    print("   1. Запустите ingest.py для загрузки документов")
    print("   2. Проверьте работу бота")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Ошибка подключения: {e}")
    print("\n💡 Убедитесь, что:")
    print("   1. Docker контейнер с БД запущен: docker-compose up -d db")
    print("   2. БД доступна на localhost:5432")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)























