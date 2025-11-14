# Product Backlog — Refinement Cycle #3

| ID | Release / Epic | Story / Task | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| BL-01 | Release 1 – Foundation | Авто ingestion/diag job’ы + документация | ✅ Done | ✅ | Документы `Yandex_AUTOMATION.md`, `diag_connectivity.py` обновлены |
| BL-02 | Release 2 – Deployment Automation | Cloud Build/Deploy конвейер (.cloudbuild, deploy-spec) | 🚀 Now | In progress | Требует настройку deploy-spec и сервисных аккаунтов на окружении |
| BL-03 | Release 3 – Knowledge Ops & Monitoring | Алерты и дашборды (Monitoring) | 🚀 Now | In progress | `monitoring_alerts.md`, дальнейшая интеграция в окружении |
| BL-04 | Cross-cutting | Перевод README/доков в UTF-8, устранение артефактов кодировки | 🟡 Next | Planned | Упростит чтение в DevTools/Cloud Build |
| BL-05 | Cross-cutting | Расширить тесты (unit для responses_client, ingest) + pytest-asyncio | 🟡 Next | Planned | Поддержка TDD/XP |
| BL-06 | Release 3 – Knowledge Ops | Авто-репорты по ingest job (usage, ошибки) | 🟡 Next | Planned | Скрипт выгрузки логов + отчёты |
| BL-07 | Release 4 – Managed RAG | Автоматизация получения `publicUrl`/`version` и обновление Lockbox | 🔵 Later | Backlog | Ожидаем доступности API |
| BL-08 | Release 4 – Advanced Insights | Учёт токенов/usage-отчёты | 🔵 Later | Backlog | Зависит от Managed RAG |
| BL-09 | Release 2 – Infra | Перенос репозитория в DevTools + автоматические хуки | 🔵 Later | Backlog | После стабилизации Cloud Build |

**Следующий инкремент:** Завершить BL-02 (подготовить deploy-spec пример и инструкции по созданию сервисных аккаунтов) и BL-03 (применить alert CLI на окружении). Каждые 3 ответа проводим новый refinement и обновляем этот файл/roadmap.
