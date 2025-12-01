import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_all_config_deps():
    with patch('config.ADMIN_ID', 12345):
        yield