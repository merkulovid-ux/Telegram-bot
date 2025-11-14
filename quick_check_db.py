"""Быстрая проверка БД - синхронный вариант"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("db:5432", "localhost:5432")

try:
    import psycopg2
    from urllib.parse import urlparse
    
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=result.hostname or "localhost",
        port=result.port or 5432,
        user=result.username or "user",
        password=result.password or "pass",
        dbname=result.path[1:] if result.path else "ai_bot",
        connect_timeout=5
    )
    cur = conn.cursor()
    
    print("="*60)
    print("📊 БАЗА ДАННЫХ")
    print("="*60)
    
    # Documents
    cur.execute("SELECT COUNT(*) FROM documents")
    docs = cur.fetchone()[0]
    print(f"\n📄 documents: {docs} записей")
    
    # knowledge_base_topics
    cur.execute("SELECT COUNT(*) FROM knowledge_base_topics")
    topics = cur.fetchone()[0]
    print(f"📚 knowledge_base_topics: {topics} тем")
    
    if topics > 0:
        cur.execute("SELECT COUNT(DISTINCT category) FROM knowledge_base_topics")
        cats = cur.fetchone()[0]
        print(f"   Категорий: {cats}")
        
        cur.execute("SELECT DISTINCT category FROM knowledge_base_topics ORDER BY category LIMIT 10")
        categories = cur.fetchall()
        print(f"\n   Категории:")
        for (cat,) in categories:
            cur.execute("SELECT COUNT(*) FROM knowledge_base_topics WHERE category = %s", (cat,))
            cnt = cur.fetchone()[0]
            print(f"   • {cat} ({cnt} тем)")
    else:
        print("   ⚠️  БАЗА ЗНАНИЙ ПУСТА! Запустите: python ingest.py")
    
    # Events
    cur.execute("SELECT COUNT(*) FROM events")
    events = cur.fetchone()[0]
    print(f"\n📈 events: {events} записей")
    
    # Feedback
    cur.execute("SELECT COUNT(*) FROM feedback")
    feedback = cur.fetchone()[0]
    print(f"💬 feedback: {feedback} записей")
    
    print("\n" + "="*60)
    
    cur.close()
    conn.close()
    print("✅ Готово")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)

