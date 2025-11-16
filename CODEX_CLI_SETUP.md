# Использование Codex CLI для работы с проектом

Этот файл помогает быстро развернуть окружение и продолжить работу с телеграм-ботом, общаясь со мной через Codex CLI.

## 1. Подготовка локальной среды
1. Установите Python 3.11+ и Docker.
2. Склонируйте репозиторий и перейдите в каталог `telegram-ai-bot`.
3. Создайте `.env` на основе `.env.example` (или `.env.prod` для облака). Убедитесь, что файл содержит реальные значения токенов и ID:
   ```bash
   cp .env.example .env
   # заполните TELEGRAM_BOT_TOKEN, DATABASE_URL, YC_* и т.д.
   ```
4. Установите зависимости для локальных скриптов:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

## 2. Запуск Codex CLI (в отдельном терминале)
1. Установите Codex CLI (подробности зависят от вашего окружения; обычно поставляется как бинарь `codex`).
2. Запустите CLI внутри каталога проекта:
   ```bash
   codex run
   ```
3. В диалоге укажите, что нужно использовать текущую папку. Далее вы сможете общаться со мной, а CLI будет автоматически подхватывать файлы репозитория.

## 3. Основные команды/скрипты
- `python check_env.py --env .env --env .env.prod` — проверка обязательных переменных перед любыми деплоями.
- `pytest tests/test_smoke.py` — быстрый smoke-тест перед коммитом/деплоем.
- `python scripts/diag_report.py` — формирование отчёта по `diag_connectivity.py` с сохранением в `diag_report.md`.
- `python scripts/generate_alert_cli.py --spec monitoring_alerts.yaml` — генерация команд `yc monitoring alert create` на основе YAML-описания.
- `python export_lockbox_payload.py --env .env --env .env.prod --output secrets.json` — подготовка payload для Lockbox.

## 4. Пайплайны и деплой
- `.cloudbuild.yaml` — пример конвейера: predeploy check → smoke-тест → docker build/push → `yc deploy release run`.
- `deploy-spec.yaml` — спецификация для Cloud Deploy; впишите реальные `container-id`, Lockbox-secretId и service-accountId.
- `Yandex_DEVOPS.md` — подробные инструкции по DevTools Repo, Cloud Build/Deploy и ролям сервисных аккаунтов.

## 5. Что передать Codex при следующем запуске
- Текущие значения `CONTAINER_ID`, `JOB_ID`, `CHANNEL_ID` (для настройки алертов).
- Результаты `diag_report.md`, если нужно проанализировать ошибки (например, недоступность БД).
- Любые логи/ошибки `docker build/push`, `yc` команд, чтобы я мог подсказать дальнейшие шаги.

Следуя этим шагам, можно быстро включить Codex CLI в рабочий цикл: вы выполняете команды/скрипты локально, а я помогаю планировать и автоматизировать следующий этап миграции.

Совет: Если вы используете CLI впервые, прочитайте README.md и другие файлы, чтобы понять контекст, Agile/TDD/XP-принципы, основные команды и работу по текущему бэклогу.