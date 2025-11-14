# Инструкция по восстановлению базы данных

## Быстрый способ (рекомендуется)

Запустите скрипт восстановления:

```bash
python restore_db_simple.py
```

Этот скрипт:
- ✅ Подключается к БД через localhost:5432
- ✅ Создает расширение vector
- ✅ Создает все необходимые таблицы
- ✅ Создает индексы
- ✅ Проверяет структуру БД

## Альтернативный способ (через Docker)

Если Python скрипт не работает, используйте Docker напрямую:

```bash
# 1. Создать расширение vector
docker exec pgvector_compose psql -U user -d ai_bot -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Применить db_init.sql
docker exec -i pgvector_compose psql -U user -d ai_bot < db_init.sql

# 3. Применить миграцию feedback
docker exec -i pgvector_compose psql -U user -d ai_bot < migrations/001_create_feedback_table.sql

# 4. Проверить таблицы
docker exec pgvector_compose psql -U user -d ai_bot -c "\dt"
```

## Проверка результата

После восстановления проверьте структуру:

```bash
python restore_db_simple.py
```

Или через Docker:

```bash
docker exec pgvector_compose psql -U user -d ai_bot -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

## Ожидаемые таблицы

После восстановления должны быть созданы:
- ✅ `documents` - для хранения документов и эмбеддингов
- ✅ `events` - для логирования событий
- ✅ `knowledge_base_topics` - для тем базы знаний
- ✅ `feedback` - для обратной связи

## Следующие шаги

После восстановления БД:
1. Запустите `python ingest.py` для загрузки документов
2. Проверьте работу бота






















