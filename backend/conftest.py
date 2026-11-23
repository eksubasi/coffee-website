import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate tests from each other's cached state (e.g. DRF throttle counters)."""
    cache.clear()
    yield
    cache.clear()
