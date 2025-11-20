# План миграции на SberCloud (Cloud.ru)

Этот документ описывает детальный пошаговый план миграции проекта "Telegram AI Bot" с Yandex Cloud на платформу SberCloud (Cloud.ru).

## Фаза 1: Исследование и PoC (Proof of Concept)

### Задача 1: Детальное исследование документации SberCloud

**Цель:** Глубоко изучить документацию SberCloud для понимания API, SDK, квот, лимитов и особенностей ценообразования.

**Чек-лист исследования:**
- [ ] **Evolution AI Factory & GigaChat:**
    - [ ] Изучить REST и gRPC API для GigaChat.
    - [ ] Понять процесс получения токенов аутентификации.
    - [ ] Изучить документацию по Managed RAG и его API.
    - [ ] Оценить возможности кастомизации и дообучения моделей (ML Finetuning).
- [ ] **Container Apps:**
    - [ ] Изучить API для развертывания контейнеров.
    - [ ] Понять, как передавать секреты и переменные окружения.
    - [ ] Изучить механизмы автомасштабирования, включая "масштабирование до нуля".
- [ ] **Managed PostgreSQL:**
    - [ ] Проверить совместимость версий PostgreSQL.
    - [ ] Изучить процесс миграции данных.
    - [ ] Понять, как настраивать доступ и безопасность.
- [ ] **Object Storage (S3):**
    - [ ] Подтвердить 100% совместимость с S3 API.
    - [ ] Изучить эндпоинты, политику доступа и ценообразование.
- [ ] **Vault:**
    - [ ] Изучить API для работы с секретами.
    - [ ] Понять, как интегрировать Vault с Container Apps и CI/CD.
- [ ] **Artifact Registry:**
    - [ ] Изучить API для загрузки Docker-образов.
    - [ ] Понять, как аутентифицироваться из GitHub Actions.
- [ ] **CI/CD (GitHub Actions):**
    - [ ] Изучить доступные GitHub Actions для SberCloud.
    - [ ] Найти примеры пайплайнов для развертывания в Container Apps.

### Задача 2: PoC - AI (GigaChat RAG) - ✅ Done

**Цель:** Создать прототип для проверки качества ответов GigaChat при работе с базой знаний проекта.

**Результат:** Создан скрипт `sbercloud_poc.py`, который демонстрирует, как использовать GigaChat API для ответов на вопросы по содержимому PDF-документа. Для запуска требуется установить переменную окружения `SBER_AUTHORIZATION_KEY`.

### Задача 3: PoC - Инфраструктура - ✅ Done

**Цель:** Развернуть базовую инфраструктуру вручную для проверки основных шагов и выявления потенциальных проблем.

**Результат:** Создано руководство `SBERCLOUD_INFRA_POC_GUIDE.md` с инструкциями по ручному созданию кластера Managed PostgreSQL, бакета в Object Storage и секрета в Vault.

---
*Этот документ будет обновляться по мере выполнения задач и получения новой информации.*

## Фаза 1: Результаты исследования

### Evolution AI Factory & GigaChat

*   **API**: Доступны REST и gRPC API. Аутентификация токен-базированная.
*   **Возможности**: Поддерживает генерацию текста и изображений. Есть руководство по составлению промптов.
*   **RAG**: Есть сервис Managed RAG, который можно использовать для интеграции с базой знаний.
*   **Документация**: [https://developers.sber.ru/docs/ru/gigachat/api/reference](https://developers.sber.ru/docs/ru/gigachat/api/reference)

### Container Apps

*   **Аналог**: Эквивалент Yandex Serverless Containers.
*   **Развертывание**: Запускает Docker-контейнеры из Artifact Registry.
*   **Масштабирование**: Поддерживает автомасштабирование, включая масштабирование до нуля.
*   **Управление**: Есть API для программного управления.
*   **Документация**: [https://cloud.ru/ru/docs/container-apps/concepts/about](https://cloud.ru/ru/docs/container-apps/concepts/about)

### Managed PostgreSQL

*   **Аналог**: Эквивалент Yandex Managed PostgreSQL.
*   **Возможности**: Высокая доступность, масштабируемость, безопасность, автоматические бэкапы.
*   **Версии**: Поддерживает PostgreSQL 9.4, 9.6, 10.4.
*   **Документация**: [https://cloud.ru/ru/docs/cloud-databases/postgresql/concepts/about](https://cloud.ru/ru/docs/cloud-databases/postgresql/concepts/about)

### Object Storage (OBS)

*   **Аналог**: Эквивалент Yandex Object Storage.
*   **Совместимость**: Полностью совместим с S3 API. Это означает, что существующий код, использующий `boto3`, должен работать с минимальными изменениями (обновление эндпоинта и учетных данных).
*   **Документация**: [https://cloud.ru/ru/docs/object-storage-advanced/concepts/about](https://cloud.ru/ru/docs/object-storage-advanced/concepts/about)

### Vault

*   **Аналог**: Эквивалент Yandex Lockbox, основан на HashiCorp Vault.
*   **Назначение**: Хранение и управление секретами.
*   **Документация**: [https://cloud.ru/ru/docs/cloud-backup-and-recovery/concepts/vault](https://cloud.ru/ru/docs/cloud-backup-and-recovery/concepts/vault) (требует уточнения, так как относится к Backup and Recovery, но вероятно, есть и отдельный сервис для секретов).

### Artifact Registry

*   **Назначение**: Аналог Yandex Container Registry для хранения Docker-образов и Helm-чартов.
*   **Интеграция с CI/CD**: Интегрируется с внешними CI/CD системами, такими как GitHub Actions, через аутентификацию с помощью сервисных аккаунтов.
*   **Документация**: [https://cloud.ru/ru/docs/artifacts/concepts/about](https://cloud.ru/ru/docs/artifacts/concepts/about)

### Vault

*   **Основа**: Основан на HashiCorp Vault.
*   **Аутентификация**: Поддерживает токены доступа, AppRole (рекомендуется для приложений), и другие методы.
*   **API**: Доступен через префикс `/v1/`.
*   **Интеграция**: Интегрируется с Container Apps для передачи секретов.
*   **Документация**: [https://cloud.ru/ru/docs/iam/vault/concepts/about](https://cloud.ru/ru/docs/iam/vault/concepts/about)

## Фаза 2: Настройка инфраструктуры и CI/CD

### Задача 4 (IaC) - In Progress

**Цель:** Начать разработку Terraform-скриптов для управления инфраструктурой на SberCloud.

**Результат:**
- Создана директория `terraform`, конфигурация провайдера SberCloud.
- Реализован модуль `modules/network` (VPC + сабнеты + security group).
- Реализован модуль `modules/managed_pg` (Managed PostgreSQL + pgvector + безопасность).
- Настроен CI (`.github/workflows/infra-cloudru.yml`) для `terraform plan/validate`.
- Обновлены переменные и примеры конфигурации.

**Следующий шаг:** подготовить OBS-бакет для state, загрузить ключи в Vault/GitHub Secrets и протестировать `terraform init/plan`.
