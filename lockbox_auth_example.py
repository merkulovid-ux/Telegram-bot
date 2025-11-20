# lockbox_auth_example.py
import os
import grpc

from yandex.cloud.lockbox.v1.payload_service_pb2 import GetPayloadRequest
from yandex.cloud.lockbox.v1.payload_service_pb2_grpc import PayloadServiceStub
from yandex.cloud.sdk import create_channel, create_default_credentials

# --- Настройка ---
# 1. Установите Yandex Cloud SDK для Python: pip install yandexcloud
# 2. Создайте сервисный аккаунт в Yandex Cloud с ролью "lockbox.viewer" или выше.
# 3. Сгенерируйте статический ключ доступа для этого сервисного аккаунта в формате JSON.
# 4. Сохраните JSON-файл ключа, например, как 'sa-key.json'.
# 5. Укажите путь к этому файлу в переменной окружения YC_SERVICE_ACCOUNT_KEY_FILE
#    или явно передайте его в create_default_credentials.
#    Пример:
#    export YC_SERVICE_ACCOUNT_KEY_FILE=/path/to/your/sa-key.json
#
#    ИЛИ
#
#    service_account_key_file = "sa-key.json" # Укажите путь к вашему файлу ключа
#    credentials = create_default_credentials(service_account_key_file=service_account_key_file)
#
# 6. Замените 'your_secret_id' на фактический ID вашего секрета в Lockbox.
# -----------------

SECRET_ID = 'your_secret_id'  # <<< ЗАМЕНИТЕ НА ID ВАШЕГО СЕКРЕТА

def get_lockbox_payload(secret_id: str):
    """
    Получает полезную нагрузку (payload) секрета из Yandex Cloud Lockbox.
    """
    try:
        # Создаем учетные данные. SDK автоматически ищет файл ключа
        # в переменной окружения YC_SERVICE_ACCOUNT_KEY_FILE.
        credentials = create_default_credentials()

        # Создаем защищенный gRPC-канал с использованием учетных данных.
        channel = create_channel(credentials=credentials)

        # Инициализируем stub для PayloadService.
        stub = PayloadServiceStub(channel)

        # Создаем запрос на получение payload секрета.
        request = GetPayloadRequest(secret_id=secret_id)

        # Выполняем запрос.
        payload = stub.Get(request)

        print(f"Payload для секрета '{secret_id}' успешно получен.")
        print("Версия секрета:", payload.current_version.version)

        # Итерируем по записям payload (ключ-значение).
        for entry in payload.entries:
            if entry.text_value:
                print(f"  Ключ: {entry.key}, Значение: {entry.text_value}")
            elif entry.data_value:
                # Если значение бинарное, можно его декодировать, если известно кодирование.
                print(f"  Ключ: {entry.key}, Значение: <бинарные данные>")
            else:
                print(f"  Ключ: {entry.key}, Значение: <пустое>")

    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {e.code().name} - {e.details()}")
        if e.code() == grpc.StatusCode.PERMISSION_DENIED:
            print("Проверьте права сервисного аккаунта. Возможно, у него нет роли 'lockbox.viewer'.")
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Секрет с ID '{secret_id}' не найден или недоступен.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

if __name__ == "__main__":
    if SECRET_ID == 'your_secret_id':
        print("Пожалуйста, замените 'your_secret_id' на актуальный ID вашего секрета в Lockbox.")
        print("Также убедитесь, что переменная окружения YC_SERVICE_ACCOUNT_KEY_FILE установлена")
        print("и указывает на файл ключа сервисного аккаунта.")
    else:
        get_lockbox_payload(SECRET_ID)
