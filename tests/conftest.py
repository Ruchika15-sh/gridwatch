import pytest

from qa_framework.client import GridWatchClient


@pytest.fixture
def api() -> GridWatchClient:
    """A fresh GridWatchClient for each test - no shared state between tests."""
    return GridWatchClient()
