import os
import json
from datetime import datetime
import grpc

# Импорты для Yandex Cloud Logging
from yandex.cloud.logging.v1.log_reading_service_pb2 import ReadRequest
from yandex.cloud.logging.v1.log_reading_service_pb2_grpc import LogReadingServiceStub

# Для аутентификации
# Так как direct SDK imports вызывали проблемы,
# будем использовать более низкоуровневый подход с gRPC и IAM-токеном/ключом SA.
# Для упрощения, предполагаем, что IAM-токен доступен через YC_IAM_TOKEN.
# В полноценном приложении стоит использовать yandexcloud SDK
# и ServiceAccountCredentials, как было показано в web-примере.
# Здесь же мы обойдемся прямым созданием канала и credential-менеджментом.

def _create_grpc_channel(target: str, iam_token: str):
    """Создает защищенный gRPC канал с IAM-токеном."""
    credentials = grpc.access_token_call_credentials(iam_token)
    return grpc.secure_channel(target, credentials)

def get_log_reading_client(iam_token: str):
    """Возвращает аутентифицированный клиент LogReadingServiceStub."""
    channel = _create_grpc_channel('logging.api.cloud.yandex.net:443', iam_token)
    return LogReadingServiceStub(channel)

def generate_ingest_report(
    folder_id: str,
    job_name: str,
    iam_token: str,
    since_hours: int = 24
) -> str:
    client = get_log_reading_client(iam_token)
    
    # Время начала чтения логов
    now = datetime.utcnow()
    since_time = now - datetime.timedelta(hours=since_hours)

    # Фильтр для логов конкретного job'а
    filter_string = (
        f'json_payload.resource.name="{job_name}" AND ' 
        f'resource.type="serverless.job" AND ' 
        f'json_payload.job_id IS NOT NULL'
    )
    
    # Запрос на чтение логов
    request = ReadRequest(
        folder_id=folder_id,
        filter=filter_string,
        since=since_time.isoformat("T") + "Z", # ISO 8601 формат
        page_size=1000 # Максимальное количество записей
    )

    successful_runs = 0
    failed_runs = 0
    error_messages = []
    total_runs = 0

    try:
        response_iterator = client.Read(request)
        for log_entry in response_iterator:
            total_runs += 1
            payload = log_entry.json_payload
            
            # Предполагаем, что статус успеха/ошибки можно извлечь из payload
            # Это может потребовать адаптации в зависимости от реального формата логов ingest_yc.py
            if payload and "event_status" in payload:
                if payload["event_status"] == "STATUS_COMPLETED":
                    successful_runs += 1
                elif payload["event_status"] == "STATUS_FAILED":
                    failed_runs += 1
                    if "message" in payload:
                        error_messages.append(payload["message"])
            elif log_entry.level == log_entry.Level.ERROR:
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

if __name__ == "__main__":
    # Для запуска скрипта локально необходимы переменные окружения
    # YC_FOLDER_ID - ID вашего каталога Yandex Cloud
    # YC_IAM_TOKEN - IAM-токен с правами на чтение логов (logging.viewer)
    
    folder_id = os.getenv("YC_FOLDER_ID")
    iam_token = os.getenv("YC_IAM_TOKEN")
    ingest_job_name = "kb-ingest-job" # Имя вашего ingest job

    if not folder_id or not iam_token:
        print("Ошибка: Отсутствуют переменные окружения YC_FOLDER_ID или YC_IAM_TOKEN.")
        print("Пожалуйста, установите их для запуска скрипта.")
        exit(1)

    print(f"Генерируем отчет для {ingest_job_name}...")
    report = generate_ingest_report(folder_id, ingest_job_name, iam_token)
    print(report)
