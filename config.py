import os
from dotenv import load_dotenv
import json
import grpc

# Импорты для работы с Lockbox
from yandex.cloud.lockbox.v1.payload_service_pb2 import GetPayloadRequest
from yandex.cloud.lockbox.v1.payload_service_pb2_grpc import PayloadServiceStub

# Импорты для SDK аутентификации из пакета yandexcloud
from yandexcloud._sdk import SDK # This is where the SDK object is


load_dotenv()

# --- Lockbox Helper Functions ---
# Реализация аутентификации Lockbox с приоритетом для ключа сервисного аккаунта.
def _get_lockbox_client():
    """
    Возвращает аутентифицированный клиент LockboxServiceStub.
    Приоритет: YC_SERVICE_ACCOUNT_KEY_FILE, затем YC_IAM_TOKEN.
    """
    sdk_instance = None
    
    # Попытка аутентификации через ключ сервисного аккаунта
    key_file_path = os.getenv("YC_SERVICE_ACCOUNT_KEY_FILE")
    if key_file_path:
        try:
            with open(key_file_path, "r") as f:
                sa_key_json = json.load(f)
            sdk_instance = SDK(service_account_key=sa_key_json)
        except FileNotFoundError:
            print(f"Ошибка: Файл ключа сервисного аккаунта не найден по пути: {key_file_path}. Попытка аутентификации через IAM-токен.")
        except Exception as e:
            print(f"Ошибка при аутентификации через ключ сервисного аккаунта: {e}. Попытка аутентификации через IAM-токен.")

    # Если аутентификация через ключ СА не удалась, пробуем IAM-токен
    if sdk_instance is None:
        iam_token = os.getenv("YC_IAM_TOKEN")
        if iam_token:
            try:
                sdk_instance = SDK(token=iam_token)
            except Exception as e:
                print(f"Ошибка при аутентификации через IAM-токен: {e}.")
        else:
            raise ValueError("Не найдены учетные данные для Lockbox. Установите YC_SERVICE_ACCOUNT_KEY_FILE или YC_IAM_TOKEN.")

    if sdk_instance is None:
        raise ValueError("Не удалось инициализировать Yandex Cloud SDK для Lockbox.")

    return sdk_instance.client(PayloadServiceStub)

def get_secret_payload(secret_id: str):
    """
    Получает содержимое секрета из Yandex Lockbox.
    """
    client = _get_lockbox_client()
    if not client:
        print("Не удалось получить клиент Lockbox. Невозможно получить секрет.")
        return None

    try:
        response = client.Get(GetPayloadRequest(secret_id=secret_id))
        print(f"Успешно получен секрет с ID: {secret_id}")
        return response

    except grpc.RpcError as e:
        print(f"Ошибка gRPC при получении секрета: {e.code()} - {e.details()}")
        if e.code() == grpc.StatusCode.PERMISSION_DENIED:
            print("Проверьте, что у сервисного аккаунта/пользователя есть роль `lockbox.viewer` для данного секрета.")
            print("Также убедитесь, что IAM-токен валиден и не истек.")
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Секрет с ID '{secret_id}' не найден или недоступен. Проверьте правильность SECRET_ID.")
        return None
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return None

# --- Configuration Loading ---
YC_LOCKBOX_SECRET_ID = os.getenv("YC_LOCKBOX_SECRET_ID")

LOCKBOX_SECRETS = {}

if YC_LOCKBOX_SECRET_ID:
    print("YC_LOCKBOX_SECRET_ID обнаружен. Попытка загрузить секреты из Lockbox...")
    
    payload = get_secret_payload(YC_LOCKBOX_SECRET_ID)
    if payload:
        for entry in payload.entries:
            if entry.text_value:
                LOCKBOX_SECRETS[entry.key] = entry.text_value
            elif entry.binary_value:
                try:
                    LOCKBOX_SECRETS[entry.key] = json.loads(entry.binary_value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    LOCKBOX_SECRETS[entry.key] = entry.binary_value.decode('utf-8')
        print("Секреты из Lockbox успешно загружены.")
    else:
        print("Не удалось загрузить секреты из Lockbox.")


def _require(name: str) -> str:
    # Проверяем сначала в Lockbox
    if name in LOCKBOX_SECRETS:
        return LOCKBOX_SECRETS[name]
    
    # Затем в переменных окружения
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Не найдена обязательная переменная окружения или секрет Lockbox: {name}")
    return value

TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")

YANDEX_API_KEY = _require("YANDEX_API_KEY")
YANDEX_FOLDER_ID = _require("YANDEX_FOLDER_ID")

# Параметры для ассистента AI Studio
YC_API_KEY = os.getenv("YC_API_KEY") or YANDEX_API_KEY
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID") or YANDEX_FOLDER_ID
YC_SEARCH_INDEX_ID = os.getenv("YC_SEARCH_INDEX_ID")
YC_ASSISTANT_ID = os.getenv("YC_ASSISTANT_ID")
YC_ASSISTANT_MODEL_URI = os.getenv("YC_ASSISTANT_MODEL_URI")

MANAGED_RAG_PUBLIC_URL = os.getenv("MANAGED_RAG_PUBLIC_URL")
MANAGED_RAG_TOKEN = os.getenv("MANAGED_RAG_TOKEN")
MANAGED_RAG_VERSION_ID = os.getenv("MANAGED_RAG_VERSION_ID")
MANAGED_RAG_MODEL = os.getenv("MANAGED_RAG_MODEL", "t-tech/T-lite-it-1.0")

DATABASE_URL = _require("DATABASE_URL")
ADMIN_ID = int(_require("ADMIN_ID"))
