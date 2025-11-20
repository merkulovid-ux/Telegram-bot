import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_all_config_deps():
    mock_ingest_yc_env = MagicMock(side_effect=lambda name, default=None: {
        "YC_OBS_BUCKET": "test-bucket",
        "YC_OBS_ACCESS_KEY_ID": "test-access-key",
        "YC_OBS_SECRET_ACCESS_KEY": "test-secret-key",
        "YC_FOLDER_ID": "test-folder-id",
        "YC_API_KEY": "test-api-key",
    }.get(name, default))

    with patch('responses_client.MANAGED_RAG_PUBLIC_URL', 'http://test-url.com'), \
         patch('responses_client.MANAGED_RAG_TOKEN', 'test-token'), \
         patch('responses_client.MANAGED_RAG_VERSION_ID', 'test-version'), \
         patch('responses_client.YC_ASSISTANT_MODEL_URI', 'test-model-uri'), \
         patch('responses_client.YC_FOLDER_ID', 'test-folder-id'), \
         patch('config.ADMIN_ID', 12345), \
         patch('ingest_yc.env', mock_ingest_yc_env):
        yield