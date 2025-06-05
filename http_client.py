from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def get_with_retry(*args: Any, **kwargs: Any) -> requests.Response:
    """Wrapper for ``requests.get`` with retry and exponential backoff."""
    return requests.get(*args, **kwargs)


@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def post_with_retry(*args: Any, **kwargs: Any) -> requests.Response:
    """Wrapper for ``requests.post`` with retry and exponential backoff."""
    return requests.post(*args, **kwargs)
