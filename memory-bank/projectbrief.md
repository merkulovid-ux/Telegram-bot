# Project Brief

- Build and maintain ProcessOff Telegram bot with RAG capabilities.
- Target infrastructure: Cloud.ru VM (no managed services for RAG); Managed PostgreSQL/Object Storage/Vault where applicable, but bot runs on VM.
- Tech stack: Python 3.11, Aiogram, LangGraph orchestration, asyncpg; **do not use Yandex**; managed RAG from Cloud.ru is not connected.
- Goals: stable bot responses, clear ops/docs, align with Cloud.ru-only stack (no Yandex).
