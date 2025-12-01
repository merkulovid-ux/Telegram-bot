# Настройка CI/CD (GitHub Actions + Cloud.ru)

Этот проект настроен на автоматический деплой при пуше в ветку `main`.

## 1. Необходимые Secrets
Для работы деплоя необходимо добавить следующие секреты в репозиторий GitHub (Settings -> Secrets and variables -> Actions):

| Имя | Значение |
| --- | --- |
| `SSH_HOST` | Публичный IP вашего сервера (176.108.252.197) |
| `SSH_USER` | Пользователь (mroneway2088) |
| `SSH_KEY` | Приватный ключ SSH (содержимое файла cloudru-vm-new) |

## 2. Container Registry (GHCR)
По умолчанию образ собирается и публикуется в GitHub Container Registry.
Чтобы сервер мог скачать образ без сложной настройки токенов, рекомендуется сделать пакет публичным:

1. После первого запуска Workflow перейдите в профиль GitHub -> Packages.
2. Найдите `telegram-ai-bot`.
3. Package Settings -> Change visibility -> **Public**.
4. Теперь `docker compose pull` будет работать без авторизации.

## 3. Процесс работы (Pipeline)
1. **Разработка:** Делайте изменения в ветке, пушьте в GitHub.
2. **Tests:** GitHub Actions автоматически прогонит тесты.
3. **Deploy:** При мерже/пуше в `main` образ соберется и обновится на сервере.
