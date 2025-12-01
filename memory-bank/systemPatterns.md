# System Patterns

- Bot runtime: `main_langgraph.py` using Aiogram + LangGraph with per-user MemorySaver (in-memory checkpoints).
- Routing: `langgraph_app.py` builds graph of nodes: route_command -> rag/assistant/conflict/kb/admin/feedback -> response.
- RAG client (current code): `responses_client.py` still assumes Yandex Search Index/Managed RAG; needs replacement to a non-Yandex/local flow. Managed RAG from Cloud.ru is not connected.
- Assistant client: `assistant_client.py` also assumes Yandex; should be bypassed/rewired for non-Yandex stack.
- Data layer: PostgreSQL via `asyncpg`; `db.py` provides a global pool; events/feedback tables.
- Logging: `analytics.log_event` best-effort (won't block on DB errors).
- Deployment: docker-compose only includes `db`; app runs as single process (systemd/Docker) with env vars on a VM.
