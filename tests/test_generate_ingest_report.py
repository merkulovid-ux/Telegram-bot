import pytest
from unittest.mock import MagicMock, patch
from scripts.generate_ingest_report import generate_ingest_report, send_telegram_message, _get_sdk_client
# Import necessary Yandex Cloud SDK components for mocking
from yandex.cloud.logging.v1.log_reading_service_pb2 import ReadRequest, Criteria, ReadResponse
from yandex.cloud.logging.v1.log_entry_pb2 import LogEntry
from yandex.cloud.logging.v1.log_entry_pb2 import LogLevel
from yandex.cloud.logging.v1.log_reading_service_pb2_grpc import LogReadingServiceStub
from yandexcloud._sdk import SDK as YCSDK # Rename SDK import to avoid conflict
import grpc # For grpc.RpcError
import httpx # Добавлен импорт httpx
import config # Для получения TELEGRAM_BOT_TOKEN и ADMIN_ID

@pytest.fixture
def mock_env_vars():
    with patch.dict(
        'os.environ',
        {
            "YC_FOLDER_ID": "mock-folder-id",
            "YC_IAM_TOKEN": "mock-iam-token",
            "TELEGRAM_BOT_TOKEN": "mock-bot-token",
            "ADMIN_ID": "12345",
            "YC_SERVICE_ACCOUNT_KEY_FILE": "/path/to/sa_key.json" # Mock service account key file path
        }
    ):
        yield

@pytest.fixture
def mock_sdk_client_and_log_reading_stub():
    with patch('scripts.generate_ingest_report.SDK') as MockSDK:
        mock_sdk_instance = MockSDK.return_value
        mock_log_reading_stub = MagicMock()
        mock_sdk_instance.client.return_value = mock_log_reading_stub
        
        # Simulate log entries
        mock_log_reading_stub.List.return_value = [
            MagicMock(entries=[
                LogEntry(json_payload={'resource': {'name': 'kb-ingest-job'}, 'event_status': 'STATUS_COMPLETED'}),
                LogEntry(json_payload={'resource': {'name': 'kb-ingest-job'}, 'event_status': 'STATUS_COMPLETED'}),
                LogEntry(json_payload={'resource': {'name': 'kb-ingest-job'}, 'event_status': 'STATUS_FAILED', 'message': 'Error parsing file'}),
                LogEntry(level=LogLevel.ERROR, message='Generic error message'),
            ])
        ]
        yield mock_sdk_instance, mock_log_reading_stub

@pytest.fixture
def mock_httpx_post():
    with patch('httpx.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post


# --- Tests for _get_sdk_client ---
def test_get_sdk_client_iam_token(mock_env_vars):
    with patch('scripts.generate_ingest_report.SDK') as MockSDK: # Patch the actual SDK class
        mock_sdk_instance = MockSDK.return_value
        sdk = _get_sdk_client(iam_token="mock-iam-token")
        MockSDK.assert_called_once_with(token="mock-iam-token")
        assert sdk == mock_sdk_instance

def test_get_sdk_client_sa_key_file(mock_env_vars, tmp_path):
    sa_key_file = tmp_path / "sa_key.json"
    sa_key_file.write_text('{"id": "test_id", "service_account_id": "test_sa_id", "private_key": "test_key"}')
    with patch.dict('os.environ', {"YC_SERVICE_ACCOUNT_KEY_FILE": str(sa_key_file)}):
        with patch('scripts.generate_ingest_report.SDK') as MockSDK: # Patch the actual SDK class
            mock_sdk_instance = MockSDK.return_value
            sdk = _get_sdk_client(service_account_key_file=str(sa_key_file))
            MockSDK.assert_called_once() # Check if SDK was called
            # Verify the service_account_key argument passed to SDK constructor
            args, kwargs = MockSDK.call_args
            assert "service_account_key" in kwargs
            assert isinstance(kwargs["service_account_key"], dict)
            assert sdk == mock_sdk_instance

def test_get_sdk_client_no_credentials_raises_error(mock_env_vars):
    with patch.dict('os.environ', clear=True): # Clear env vars to simulate no credentials
        with pytest.raises(ValueError, match="Не найдены учетные данные для Yandex Cloud SDK"):
            _get_sdk_client()

# --- Tests for send_telegram_message ---
def test_send_telegram_message_success(mock_httpx_post):
    send_telegram_message("bot_token", 123, "Test message")
    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    assert "api.telegram.org" in args[0]
    assert kwargs['json']['chat_id'] == 123
    assert kwargs['json']['text'] == "Test message"

def test_send_telegram_message_http_error(mock_httpx_post):
    mock_httpx_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=MagicMock(status_code=400, text="Bad Request"))
    with patch('builtins.print') as mock_print:
        send_telegram_message("bot_token", 123, "Test message")
        mock_print.assert_any_call(
            "Ошибка HTTP при отправке сообщения в Telegram: 400 - Bad Request"
        )

def test_send_telegram_message_request_error(mock_httpx_post):
    mock_httpx_post.side_effect = httpx.RequestError("Network Error", request=MagicMock())
    with patch('builtins.print') as mock_print:
        send_telegram_message("bot_token", 123, "Test message")
        mock_print.assert_any_call(
            "Ошибка при запросе к Telegram Bot API: Network Error"
        )

# --- Tests for generate_ingest_report ---
def test_generate_ingest_report_success(mock_env_vars, mock_sdk_client_and_log_reading_stub):
    mock_sdk_instance, mock_log_reading_stub = mock_sdk_client_and_log_reading_stub
    
    report = generate_ingest_report(
        "mock-folder-id", "kb-ingest-job", iam_token="mock-iam-token"
    )
    assert "Отчет по ingest job 'kb-ingest-job' за последние 24 часов" in report
    assert "Всего попыток запуска: 4" in report
    assert "Успешных запусков: 2" in report
    assert "Проваленных запусков: 2" in report
    assert "Подробности ошибок:" in report
    assert "- Error parsing file" in report
    assert "- Generic error message" in report

def test_generate_ingest_report_no_errors(mock_env_vars, mock_sdk_client_and_log_reading_stub):
    mock_sdk_instance, mock_log_reading_stub = mock_sdk_client_and_log_reading_stub
    mock_log_reading_stub.List.return_value = [
        MagicMock(entries=[
            LogEntry(json_payload={'resource': {'name': 'kb-ingest-job'}, 'event_status': 'STATUS_COMPLETED'}),
            LogEntry(json_payload={'resource': {'name': 'kb-ingest-job'}, 'event_status': 'STATUS_COMPLETED'}),
        ])
    ]
    report = generate_ingest_report(
        "mock-folder-id", "kb-ingest-job", iam_token="mock-iam-token"
    )
    assert "Ошибок не обнаружено." in report

def test_generate_ingest_report_sdk_init_error():
    report = generate_ingest_report(
        "mock-folder-id", "kb-ingest-job", iam_token=None, service_account_key_file=None
    )
    assert "Ошибка инициализации SDK для чтения логов: Не найдены учетные данные для Yandex Cloud SDK" in report

# --- Tests for main function ---
def test_main_function_sends_telegram_message(mock_env_vars, mock_sdk_client_and_log_reading_stub, mock_httpx_post):
    with patch('scripts.generate_ingest_report.generate_ingest_report', return_value="Test Report"):
        with patch('scripts.generate_ingest_report.print') as mock_print:
            with patch('config.TELEGRAM_BOT_TOKEN', "mock-bot-token"): # Patch config directly
                with patch('config.ADMIN_ID', 123): # Patch config directly
                    import scripts.generate_ingest_report as ingest_report_script
                    ingest_report_script.main() # Call main directly
                    mock_print.assert_any_call("Генерируем отчет для kb-ingest-job...")
                    mock_print.assert_any_call("Test Report")
                    mock_httpx_post.assert_called_once()