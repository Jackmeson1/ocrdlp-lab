import pytest
from unittest.mock import patch
import requests

from gpt4v_image_labeler import GPT4VImageLabeler


@pytest.mark.asyncio
async def test_classify_image_timeout():
    labeler = GPT4VImageLabeler("key")
    with (
        patch.object(labeler, "encode_image", return_value="dGVzdA=="),
        patch.object(labeler, "get_image_info", return_value={"info": True}),
        patch("requests.post", side_effect=requests.exceptions.Timeout),
    ):
        result = await labeler.classify_image("img.jpg")
    assert result["error"] == "API request timed out"
    assert result["_metadata"]["image_path"] == "img.jpg"
    assert result["_metadata"]["image_info"] == {"info": True}


@pytest.mark.asyncio
async def test_classify_image_request_exception():
    labeler = GPT4VImageLabeler("key")
    with (
        patch.object(labeler, "encode_image", return_value="dGVzdA=="),
        patch.object(labeler, "get_image_info", return_value={"info": True}),
        patch("requests.post", side_effect=requests.exceptions.RequestException("fail")),
    ):
        result = await labeler.classify_image("img.jpg")
    assert result["error"].startswith("Network error")
    assert result["_metadata"]["image_path"] == "img.jpg"


@pytest.mark.asyncio
async def test_classify_image_general_exception():
    labeler = GPT4VImageLabeler("key")
    with (
        patch.object(labeler, "encode_image", return_value="dGVzdA=="),
        patch.object(labeler, "get_image_info", return_value={"info": True}),
        patch("requests.post", side_effect=ValueError("boom")),
    ):
        result = await labeler.classify_image("img.jpg")
    assert result["error"].startswith("请求异常:")
    assert result["_metadata"]["image_path"] == "img.jpg"
