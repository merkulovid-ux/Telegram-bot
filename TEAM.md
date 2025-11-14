# Виртуальная проектная команда

Документация в `Documents\Agilta\retrospective\roles\roles` использована как база для построения внутренней виртуальной команды; приоритизацию и распределение задач в этом репозитории мы выстраиваем по этим ролям.

## Роли и зоны ответственности

| Роль | Источник | Основные сферы влияния |
| --- | --- | --- |
| Scrum Master | `6_scrum_master.md` | Защищает Scrum-события (Planning, Daily, Review, Retrospective), следит за DoR/DoD, координирует Product Owner и снимает препоны. |
| Backend / Integration Engineer | `13_backend_engineer.md` | Инжиниринг API, надёжность, безопасность, embedding, метаданные, автоматизация загрузки и связка с AI Studio. |
| DevOps / Release` | `17_devops_engineer.md` | CI/CD, docker-compose, мониторинг, SLO/SLI, автоматизированные релизы, настройка Object Storage и healthchecks. |
| QA Lead | `14_quality_lead.md` | Definition of Ready/Done, тестовые стратегии (unit, integration, e2e, manual), контрактные прогонки и поддержка стабильности. |
| Product Owner & Analytics | `8_product_owner.md`, `15_analytics_lead.md` | Приоритизация фич, метрики, сбор обратной связи и принятие решения о следующем MVP. |

## Принципы взаимодействия

- Каждой задаче из `BACKLOG.md` назначается ведущая роль (см. таблицу там) и, при необходимости, вспомогательная роль. Эта комбинация обеспечивает поток информации: PO → Scrum Master → DevOps/Backend → QA.
- Любую новую инициативу оформляем как карточку с `ID`, `Role`, `Expected Result` и статусом. Все переходы (например, запрос от PO к DevOps или передача QA к Backend) документируются в том же списке.
- При обработке пользовательских запросов команда использует модели, описанные в `assistant_client.py`, и включает `threads`, `citations`, `kb_metadata`, чтобы сохранить traceability между ролями.

## Что делать дальше

1. Запустить задачи с наивысшим приоритетом (ID 1‑3) и попросить Scrum Master обновить процессный чеклист.
2. Передавать результаты QA Lead сразу в `BACKLOG.md` (в колонке `Образ результата`) и отмечать статус `In progress`/`To do`/`Done`.
3. При развитии новых функций (WebSearch, Batch Inference, Cloud Function) координировать инициативу между DevOps + Backend и сразу фиксировать требуемый `assistant`/`Search Index`/`Object Storage`.

Это позволит чётко видеть, кто отвечает за статус и кто следующий на очереди после завершения шага.
