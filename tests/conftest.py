import pytest
import tenacity


@pytest.fixture(autouse=True)
def disable_tenacity_sleep(monkeypatch):
    """Speed up tests by disabling tenacity's sleep."""
    monkeypatch.setattr(tenacity, "nap", lambda _: None)
    yield
