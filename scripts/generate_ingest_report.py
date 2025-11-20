import os
import json
from datetime import datetime, timedelta
import httpx
import config # Для получения TELEGRAM_BOT_TOKEN и ADMIN_ID
import grpc

# Импорты для Yandex Cloud Logging
from yandex.cloud.logging.v1.log_reading_service_pb2 import ReadRequest, Criteria # Corrected
from yandex.cloud.logging.v1.log_reading_service_pb2_grpc import LogReadingServiceStub
from yandex.cloud.logging.v1.log_entry_pb2 import LogEntry # Corrected import for LogEntry
from yandex.cloud.logging.v1.log_entry_pb2 import LogLevel # Corrected import for LogLevel

# Импорт для Yandex Cloud SDK
from yandexcloud._sdk import SDK

# --- Yandex Cloud Logging Helper Functions ---
def _get_sdk_client(iam_token: str = None, service_account_key_file: str = None) -> SDK:
    """Инициализирует SDK клиент Yandex Cloud с IAM-токеном или ключом сервисного аккаунта."""
    if service_account_key_file:
        try:
            with open(service_account_key_file, "r") as f:
                sa_key_json = json.load(f)
            return SDK(service_account_key=sa_key_json)
        except FileNotFoundError:
            print(f"Ошибка: Файл ключа сервисного аккаунта не найден по пути: {service_account_key_file}.")
        except Exception as e:
            print(f"Ошибка при аутентификации через ключ сервисного аккаунта: {e}.")
    
    if iam_token:
        try:
            return SDK(token=iam_token)
        except Exception as e:
            print(f"Ошибка при аутентификации через IAM-токен: {e}.")
            
    raise ValueError("Не найдены учетные данные для Yandex Cloud SDK. Установите YC_IAM_TOKEN или YC_SERVICE_ACCOUNT_KEY_FILE.")


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


def generate_ingest_report(
    folder_id: str,
    job_name: str,
    iam_token: str = None,
    service_account_key_file: str = None,
    since_hours: int = 24
) -> str:
    """
    Генерирует отчет по ingest job, читая логи из Yandex Cloud Logging.
    """
    try:
        sdk = _get_sdk_client(iam_token=iam_token, service_account_key_file=service_account_key_file)
        client = sdk.client(LogReadingServiceStub)
    except ValueError as e:
        return f"Ошибка инициализации SDK для чтения логов: {e}"
    except Exception as e:
        return f"Непредвиденная ошибка при инициализации SDK для чтения логов: {e}"
    
    # Время начала чтения логов
    now = datetime.utcnow()
    since_time = now - timedelta(hours=since_hours)

    # Фильтр для логов конкретного job'а, теперь включает folder_id
    filter_string = (
        f'folder_id="{folder_id}" AND ' # Добавляем folder_id в фильтр
        f'json_payload.resource.name="{job_name}" AND '
        f'resource.type="serverless.job" AND '
        f'json_payload.job_id IS NOT NULL'
    )
    
    # Запрос на чтение логов
    request = ReadRequest(
        criteria=Criteria(
            filter=filter_string,
            since=since_time, # datetime object
            page_size=1000 # Максимальное количество записей
        )
    )

    successful_runs = 0
    failed_runs = 0
    error_messages = []
    total_runs = 0

    try:
        response_iterator = client.List(request) # Corrected to client.List
        for response_entry in response_iterator: # client.List returns an iterator of ListLogsResponse
            for log_entry in response_entry.entries: # Each response has a list of entries
                total_runs += 1
                payload = log_entry.json_payload
                
                # Предполагаем, что статус успеха/ошибки можно извлечь из payload
                if payload and "event_status" in payload:
                    if payload["event_status"] == "STATUS_COMPLETED":
                        successful_runs += 1
                    elif payload["event_status"] == "STATUS_FAILED":
                        failed_runs += 1
                        if "message" in payload:
                            error_messages.append(payload["message"])
                elif log_entry.level == LogLevel.ERROR: # Corrected
                    failed_runs += 1
                    error_messages.append(log_entry.message)


    except grpc.RpcError as e:
        return f"Ошибка gRPC при чтении логов: {e.details()} (Code: {e.code().name})"
    except Exception as e:
        return f"Непредвиденная ошибка при чтении логов: {e}"

    report = f"Отчет по ingest job '{job_name}' за последние {since_hours} часов:\n"
    report += f"Всего попыток запуска: {total_runs}\n"
    report += f"Успешных запусков: {successful_runs}\n"
    report += f"Проваленных запусков: {failed_runs}\n"

    if error_messages:
        report += "\nПодробности ошибок:\n"
        for msg in error_messages:
            report += f"- {msg}\n"
    else:
        report += "Ошибок не обнаружено.\n"
    
    return report

def main():
    # Для запуска скрипта локально необходимы переменные окружения
    # YC_FOLDER_ID - ID вашего каталога Yandex Cloud
    # YC_IAM_TOKEN или YC_SERVICE_ACCOUNT_KEY_FILE - учетные данные для доступа к Yandex Cloud
    
    folder_id = os.getenv("YC_FOLDER_ID")
    iam_token = os.getenv("YC_IAM_TOKEN")
    service_account_key_file = os.getenv("YC_SERVICE_ACCOUNT_KEY_FILE")
    ingest_job_name = "kb-ingest-job" # Имя вашего ingest job

    if not folder_id:
        print("Ошибка: Отсутствует переменная окружения YC_FOLDER_ID.")
        exit(1)
    
    if not iam_token and not service_account_key_file:
        print("Ошибка: Отсутствуют переменные окружения YC_IAM_TOKEN или YC_SERVICE_ACCOUNT_KEY_FILE для аутентификации.")
        exit(1)

    # Проверка наличия токена и ID админа для Telegram
    if not config.TELEGRAM_BOT_TOKEN or not config.ADMIN_ID:
        print("Ошибка: Отсутствуют переменные окружения TELEGRAM_BOT_TOKEN или ADMIN_ID в config.py.")
        print("Пожалуйста, установите их для запуска скрипта и отправки уведомлений.")
        exit(1)

    print(f"Генерируем отчет для {ingest_job_name}...")
    report = generate_ingest_report(
        folder_id=folder_id,
        job_name=ingest_job_name,
        iam_token=iam_token,
        service_account_key_file=service_account_key_file
    )
    print(report)
    
    # Отправляем отчет в Telegram, если доступны токен и ID админа
    send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.ADMIN_ID, report)

if __name__ == "__main__":
    main()