"""
Скрипт для проверки данных в базе знаний (команда /kb)
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

print("🔍 Проверка данных в базе знаний...")
print(f"📡 Подключение к: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}\n")

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
    cur = conn.cursor()
    
    print("="*60)
    print("📊 СТАТИСТИКА ПО ТАБЛИЦАМ")
    print("="*60)
    
    # 1. Таблица documents
    cur.execute("SELECT COUNT(*) FROM documents;")
    docs_count = cur.fetchone()[0]
    print(f"\n📄 Таблица 'documents': {docs_count} записей")
    
    if docs_count > 0:
        cur.execute("SELECT COUNT(DISTINCT source) FROM documents;")
        unique_sources = cur.fetchone()[0]
        print(f"   Уникальных источников: {unique_sources}")
        
        cur.execute("SELECT source, COUNT(*) as cnt FROM documents GROUP BY source ORDER BY cnt DESC LIMIT 5;")
        top_sources = cur.fetchall()
        if top_sources:
            print("   Топ-5 источников:")
            for source, cnt in top_sources:
                print(f"     - {os.path.basename(source) if source else 'unknown'}: {cnt} чанков")
    
    # 2. Таблица knowledge_base_topics (для команды /kb)
    print(f"\n📚 Таблица 'knowledge_base_topics' (для команды /kb):")
    cur.execute("SELECT COUNT(*) FROM knowledge_base_topics;")
    topics_count = cur.fetchone()[0]
    print(f"   Всего тем: {topics_count}")
    
    if topics_count > 0:
        cur.execute("SELECT COUNT(DISTINCT category) FROM knowledge_base_topics;")
        categories_count = cur.fetchone()[0]
        print(f"   Категорий: {categories_count}")
        
        print(f"\n   📁 Категории и темы:")
        cur.execute("SELECT DISTINCT category FROM knowledge_base_topics ORDER BY category;")
        categories = cur.fetchall()
        
        for (category,) in categories:
            cur.execute("SELECT COUNT(*) FROM knowledge_base_topics WHERE category = %s;", (category,))
            topic_count = cur.fetchone()[0]
            print(f"\n   📂 {category} ({topic_count} тем):")
            
            cur.execute("SELECT topic FROM knowledge_base_topics WHERE category = %s ORDER BY id LIMIT 10;", (category,))
            topics = cur.fetchall()
            for (topic,) in topics:
                print(f"      • {topic}")
            
            if topic_count > 10:
                print(f"      ... и еще {topic_count - 10} тем")
    else:
        print("   ⚠️  База знаний пуста! Запустите ingest.py для загрузки документов.")
    
    # 3. Таблица events
    cur.execute("SELECT COUNT(*) FROM events;")
    events_count = cur.fetchone()[0]
    print(f"\n📈 Таблица 'events': {events_count} записей")
    
    if events_count > 0:
        cur.execute("SELECT command, COUNT(*) as cnt FROM events GROUP BY command ORDER BY cnt DESC LIMIT 5;")
        top_commands = cur.fetchall()
        if top_commands:
            print("   Топ-5 команд:")
            for cmd, cnt in top_commands:
                print(f"     - {cmd}: {cnt} использований")
    
    # 4. Таблица feedback
    cur.execute("SELECT COUNT(*) FROM feedback;")
    feedback_count = cur.fetchone()[0]
    print(f"\n💬 Таблица 'feedback': {feedback_count} записей")
    
    print("\n" + "="*60)
    print("✅ Проверка завершена")
    print("="*60)
    
    if topics_count == 0:
        print("\n⚠️  ВНИМАНИЕ: База знаний пуста!")
        print("   Для загрузки данных выполните:")
        print("   python ingest.py")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Ошибка подключения: {e}")
    print("\n💡 Убедитесь, что:")
    print("   1. Docker контейнер с БД запущен: docker-compose up -d db")
    print("   2. БД доступна на localhost:5432")
    sys.exit(1)
except psycopg2.ProgrammingError as e:
    print(f"\n❌ Ошибка SQL: {e}")
    print("\n💡 Возможно, таблицы еще не созданы. Запустите:")
    print("   python restore_db_simple.py")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)






















