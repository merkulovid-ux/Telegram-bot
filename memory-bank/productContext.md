# Product Context

- Telegram bot for Agile/Scrum support: answer questions from knowledge base, produce digests, SWOT/NVC, retro/icebreaker helpers.
- Users: team members (PO, Scrum Master, Dev/QA) needing quick guidance and KB access.
- Content source: PDFs/TXT/MD in `data_pdfs/knowledge_base`; ingestion/indexing is local/VM-based (no Yandex, no managed RAG).
- Experience goals: fast answers, graceful degradation (bot replies even if logging/DB is down), simple command set.
