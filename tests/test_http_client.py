from unittest.mock import Mock

import pytest
import requests

from http_client import get_with_retry, post_with_retry


def test_get_with_retry_success_after_failure(monkeypatch):
    calls = {
        "count": 0,
    }

    def fail_then_pass(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 2:
            raise requests.exceptions.Timeout("boom")
        return Mock(status_code=200)

    monkeypatch.setattr(requests, "get", fail_then_pass)

    resp = get_with_retry("http://example.com")
    assert resp.status_code == 200
    assert calls["count"] == 2


def test_post_with_retry_raises(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.exceptions.Timeout()),
    )
    with pytest.raises(requests.exceptions.Timeout):
        post_with_retry("http://example.com")
