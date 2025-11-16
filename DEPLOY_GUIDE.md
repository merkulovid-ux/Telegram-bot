# Инструкция по развертыванию Telegram-бота на сервере

Это руководство поможет вам перенести бота на ваш сервер `reg.ru`, чтобы он работал 24/7.

## Предварительные требования

1.  **Доступ к серверу по SSH**: У вас должны быть IP-адрес, логин (обычно `root` или другой пользователь) и пароль или SSH-ключ для подключения.
2.  **Операционная система Linux**: Инструкция написана для серверов на базе Debian/Ubuntu, что является стандартом для большинства хостинг-провайдеров, включая `reg.ru`.

---

## Шаг 1: Подготовка локального проекта к переносу

Самый надежный способ перенести проект — использовать систему контроля версий **Git** и сервис **GitHub** (или GitLab, Bitbucket).

1.  **Создайте приватный репозиторий на GitHub**:
    *   Зайдите на [GitHub](https://github.com) и создайте новый **приватный** репозиторий (например, `telegram-ai-bot`). Приватный — чтобы никто не видел ваш код.

2.  **Инициализируйте Git в вашем проекте** (если еще не сделали):
    *   Откройте терминал в папке с ботом (`C:\Users\U_M16X2\telegram-ai-bot`) и выполните команды:
    ```bash
git init
git add .
git commit -m "Initial commit"
    ```

3.  **Свяжите локальный проект с репозиторием на GitHub**:
    *   Скопируйте URL вашего репозитория и выполните команды:
    ```bash
git remote add origin <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
git branch -M main
git push -u origin main
    ```

Теперь ваш код в безопасности и готов к переносу на сервер.

---

## Шаг 2: Настройка сервера

1.  **Подключитесь к серверу по SSH**:
    ```bash
ssh ваш_логин@IP_адрес_вашего_сервера
    ```

2.  **Установите Docker и Docker Compose**:
    *   Это самая важная часть. Выполните следующие команды на сервере, чтобы установить все необходимое:
    ```bash
# Обновляем списки пакетов
sudo apt-get update

# Устанавливаем необходимые пакеты
sudo apt-get install -y ca-certificates curl gnupg

# Добавляем официальный GPG-ключ Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Настраиваем репозиторий Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Устанавливаем Docker Engine и Compose
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

3.  **Установите Git** (если его еще нет):
    ```bash
sudo apt-get install -y git
    ```

---

## Шаг 3: Развертывание бота на сервере

1.  **Клонируйте ваш проект из GitHub**:
    *   На сервере выполните команду:
    ```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
    ```
    *   Перейдите в папку с проектом:
    ```bash
cd telegram-ai-bot
    ```

2.  **Создайте файл с секретами (`.env`)**:
    *   Этот файл **не** копируется из Git. Его нужно создать прямо на сервере.
    *   Выполните команду, чтобы создать и начать редактировать файл:
    ```bash
nano .env
    ```
    *   Вставьте в него ваши секретные ключи. **ВАЖНО**: `DATABASE_URL` должен указывать на `db`, так как контейнеры будут в одной Docker-сети.
    ```
TELEGRAM_BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_ТОКЕН
YANDEX_API_KEY=ВАШ_YANDEX_API_KEY
YC_FOLDER_ID=ВАШ_YC_FOLDER_ID
DATABASE_URL=postgres://user:pass@db:5432/ai_bot
    ```
    *   Нажмите `Ctrl+X`, затем `Y` и `Enter`, чтобы сохранить и выйти из редактора `nano`.

3.  **Создайте папку для документов** (если планируете загружать их на сервере):
    ```bash
mkdir -p data_pdfs
    ```

4.  **Соберите и запустите бота**:
    *   В папке проекта (`telegram-ai-bot`) выполните команду:
    ```bash
docker-compose up -d --build
    ```
    *   `-d` (detached) — запуск в фоновом режиме.
    *   `--build` — принудительная пересборка образа с вашим кодом.

---

## Готово!

Ваш бот теперь работает на сервере в Docker-контейнере. Он будет доступен 24/7 и автоматически перезапустится, если сервер будет перезагружен.

### Полезные команды на сервере:

*   **Посмотреть логи бота**: `docker-compose logs -f app`
*   **Остановить бота**: `docker-compose down`
*   **Обновить бота после изменений в коде**:
    1.  `git pull` (скачать новую версию кода из GitHub)
    2.  `docker-compose up -d --build` (пересобрать и перезапустить)

## Yandex Cloud
Подробности см. Yandex_DEPLOY.md для настройки Serverless Container, Search Index и Managed RAG.