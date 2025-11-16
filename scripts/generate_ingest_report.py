import os
from datetime import datetime, timedelta
import httpx
import config # Для получения TELEGRAM_BOT_TOKEN и ADMIN_ID

# --- Заглушка для Yandex Cloud Logging интеграции ---
# Временно, чтобы разблокировать тестирование и основную логику отчета.
# Полная интеграция с Yandex Cloud Logging (yc logging read) будет реализована
# после стабилизации Yandex Cloud SDK или через вызов yc CLI в Serverless Function.

def generate_ingest_report(
    folder_id: str,
    job_name: str,
    iam_token: str,
    since_hours: int = 24
) -> str:
    """
    Генерирует заглушку отчета по ingest job.
    В будущем здесь будет реальная логика чтения логов Yandex Cloud Logging.
    """
    # Dummy data for the report
    total_runs = 5
    successful_runs = 4
    failed_runs = 1
    error_messages = ["Ошибка: файл 'invalid.pdf' не обработан."]

    report = f"Отчет по ingest job '{job_name}' (заглушка) за последние {since_hours} часов:\n"
    report += f"Всего попыток запуска: {total_runs}\n"
    report += f"Успешных запусков: {successful_runs}\n"
    report += f"Проваленных запусков: {failed_runs}\n"

    if error_messages:
        report += "\nПодробности ошибок:\n"
        for msg in error_messages:
            report += f"- {msg}\n"
    else:
        report += "Ошибок не обнаружено.\n"
    
    report += "\n(Примечание: это заглушка отчета, реальная интеграция с Yandex Cloud Logging будет реализована.)"
    
    return report

def send_telegram_message(bot_token: str, chat_id: int, message: str):
    """Отправляет сообщение в Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Сообщение успешно отправлено в Telegram чат {chat_id}.")
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP при отправке сообщения в Telegram: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Ошибка при запросе к Telegram Bot API: {e}")

def main():
    # Для запуска скрипта локально необходимы переменные окружения
    # YC_FOLDER_ID - ID вашего каталога Yandex Cloud
    # YC_IAM_TOKEN - IAM-токен с правами на чтение логов (logging.viewer)
    
    folder_id = os.getenv("YC_FOLDER_ID") or "dummy-folder-id" # Заглушка
    iam_token = os.getenv("YC_IAM_TOKEN") or "dummy-iam-token" # Заглушка
    ingest_job_name = "kb-ingest-job" # Имя вашего ingest job

    # Проверка наличия токена и ID админа для Telegram
    if not config.TELEGRAM_BOT_TOKEN or not config.ADMIN_ID:
        print("Ошибка: Отсутствуют переменные окружения TELEGRAM_BOT_TOKEN или ADMIN_ID в config.py.")
        print("Пожалуйста, установите их для запуска скрипта и отправки уведомлений.")
        exit(1)

    print(f"Генерируем отчет для {ingest_job_name}...")
    report = generate_ingest_report(folder_id, ingest_job_name, iam_token)
    print(report)
    
    # Отправляем отчет в Telegram, если доступны токен и ID админа
    send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.ADMIN_ID, report)

if __name__ == "__main__":
    main()
