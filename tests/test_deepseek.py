import json

import httpx
import pytest

from app.config import AppConfig
from app.services.deepseek import DeepSeekClient, DeepSeekError


def test_missing_api_key_has_actionable_error():
    client = DeepSeekClient(AppConfig(api_key=""))

    with pytest.raises(DeepSeekError, match="config.local.json"):
        client.chat([{"role": "user", "content": "你好"}])


def test_successful_request_uses_expected_endpoint_and_payload():
    captured = {}

    def handler(request: httpx.Request):
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "练习回复"}}]},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    config = AppConfig(
        api_key="test-secret",
        base_url="https://api.example.test",
        model="deepseek-chat",
    )

    try:
        result = DeepSeekClient(config, http_client).chat(
            [{"role": "user", "content": "你好"}]
        )
    finally:
        http_client.close()

    assert result == "练习回复"
    assert captured["url"] == "https://api.example.test/chat/completions"
    assert captured["authorization"] == "Bearer test-secret"
    assert captured["body"]["model"] == "deepseek-chat"
    assert captured["body"]["stream"] is False


def test_streaming_request_yields_sse_content_in_order():
    captured = {}
    stream_body = "\n".join(
        [
            'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}',
            "",
            'data: {"choices":[{"delta":{"content":"第一段"}}]}',
            "",
            'data: {"choices":[{"delta":{"content":"第二段"}}]}',
            "",
            "data: [DONE]",
            "",
        ]
    )

    def handler(request: httpx.Request):
        captured["body"] = json.loads(request.content)
        captured["accept"] = request.headers["Accept"]
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=stream_body.encode("utf-8"),
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    config = AppConfig(api_key="test-secret", base_url="https://api.example.test")
    try:
        chunks = list(
            DeepSeekClient(config, http_client).stream_chat(
                [{"role": "user", "content": "你好"}]
            )
        )
    finally:
        http_client.close()

    assert chunks == ["第一段", "第二段"]
    assert captured["body"]["stream"] is True
    assert captured["accept"] == "text/event-stream"


def test_empty_stream_is_reported_as_invalid_data():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"data: [DONE]\n\n")
    )
    http_client = httpx.Client(transport=transport)
    try:
        with pytest.raises(DeepSeekError, match="无法识别"):
            list(DeepSeekClient(AppConfig(api_key="test"), http_client).stream_chat([]))
    finally:
        http_client.close()


@pytest.mark.parametrize(
    "status, expected",
    [
        (401, "API Key"),
        (429, "频繁|额度"),
        (500, "暂时不可用"),
    ],
)
def test_http_errors_are_user_safe(status, expected):
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    http_client = httpx.Client(transport=transport)
    config = AppConfig(api_key="must-not-appear")

    try:
        with pytest.raises(DeepSeekError, match=expected) as error:
            DeepSeekClient(config, http_client).chat([])
    finally:
        http_client.close()

    assert "must-not-appear" not in str(error.value)
