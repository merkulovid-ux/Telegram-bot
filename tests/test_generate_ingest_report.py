import pytest
from unittest.mock import MagicMock, patch
from scripts.generate_ingest_report import generate_ingest_report, send_telegram_message
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
        }
    ):
        yield

@pytest.fixture
def mock_httpx_post():
    with patch('httpx.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post

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

def test_generate_ingest_report_dummy_content():
    report = generate_ingest_report(
        "mock-folder-id", "kb-ingest-job", "mock-iam-token"
    )
    assert "Отчет по ingest job 'kb-ingest-job' (заглушка) за последние 24 часов" in report
    assert "Всего попыток запуска: 5" in report
    assert "Успешных запусков: 4" in report
    assert "Проваленных запусков: 1" in report
    assert "Подробности ошибок:" in report
    assert "- Ошибка: файл 'invalid.pdf' не обработан." in report
    assert "(Примечание: это заглушка отчета, реальная интеграция с Yandex Cloud Logging будет реализована.)" in report

def test_main_function_sends_telegram_message(mock_env_vars, mock_httpx_post):
    with patch('scripts.generate_ingest_report.generate_ingest_report', return_value="Test Report"):
        with patch('scripts.generate_ingest_report.print') as mock_print:
            with patch('config.TELEGRAM_BOT_TOKEN', "mock-bot-token"): # Patch config directly
                with patch('config.ADMIN_ID', 123): # Patch config directly
                    # Import the module to get a reference to the main function
                    import scripts.generate_ingest_report as ingest_report_script
                    ingest_report_script.main() # Call main directly
                    mock_print.assert_any_call("Генерируем отчет для kb-ingest-job...")
                    mock_print.assert_any_call("Test Report")
                    mock_httpx_post.assert_called_once()
