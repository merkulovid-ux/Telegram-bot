"""Простой скрипт для проверки содержимого БД"""
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from config import DATABASE_URL
import asyncpg

async def check_db():
    # Заменяем db на localhost
    db_url = DATABASE_URL.replace("db:5432", "localhost:5432") if "db:5432" in DATABASE_URL else DATABASE_URL
    
    try:
        conn = await asyncpg.connect(db_url)
        
        print("="*60)
        print("📊 СОДЕРЖИМОЕ БАЗЫ ДАННЫХ")
        print("="*60)
        
        # 1. Documents
        count = await conn.fetchval("SELECT COUNT(*) FROM documents")
        print(f"\n📄 documents: {count} записей")
        
        if count > 0:
            sources = await conn.fetchval("SELECT COUNT(DISTINCT source) FROM documents")
            print(f"   Уникальных источников: {sources}")
        
        # 2. knowledge_base_topics (для /kb)
        print(f"\n📚 knowledge_base_topics (для команды /kb):")
        topics_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base_topics")
        print(f"   Всего тем: {topics_count}")
        
        if topics_count > 0:
            cats_count = await conn.fetchval("SELECT COUNT(DISTINCT category) FROM knowledge_base_topics")
            print(f"   Категорий: {cats_count}")
            
            print(f"\n   📁 Категории:")
            categories = await conn.fetch("SELECT DISTINCT category FROM knowledge_base_topics ORDER BY category")
            
            for row in categories:
                cat = row['category']
                topic_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM knowledge_base_topics WHERE category = $1", cat
                )
                print(f"\n   📂 {cat} ({topic_count} тем):")
                
                topics = await conn.fetch(
                    "SELECT topic FROM knowledge_base_topics WHERE category = $1 ORDER BY id LIMIT 5",
                    cat
                )
                for t in topics[:5]:
                    print(f"      • {t['topic']}")
                if topic_count > 5:
                    print(f"      ... и еще {topic_count - 5} тем")
        else:
            print("   ⚠️  БАЗА ЗНАНИЙ ПУСТА!")
            print("   Запустите: python ingest.py")
        
        # 3. Events
        events = await conn.fetchval("SELECT COUNT(*) FROM events")
        print(f"\n📈 events: {events} записей")
        
        # 4. Feedback
        feedback = await conn.fetchval("SELECT COUNT(*) FROM feedback")
        print(f"\n💬 feedback: {feedback} записей")
        
        print("\n" + "="*60)
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_db())

