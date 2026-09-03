from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import httpx

from app.config import AppConfig


class DeepSeekError(RuntimeError):
    """A user-safe DeepSeek request error that never includes the API key."""


class DeepSeekClient:
    def __init__(self, config: AppConfig, client: httpx.Client | None = None):
        self._config = config
        self._client = client

    def chat(self, messages: Sequence[dict[str, str]]) -> str:
        self._ensure_configured()

        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=self._config.timeout_seconds)
        try:
            response = client.post(
                self._endpoint,
                headers=self._headers,
                json=self._payload(messages, stream=False),
            )
            response.raise_for_status()
            return self._extract_content(response.json())
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise self._user_safe_error(exc) from exc
        finally:
            if owns_client:
                client.close()

    def stream_chat(self, messages: Sequence[dict[str, str]]):
        """Yield text fragments from DeepSeek's SSE response."""
        self._ensure_configured()

        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=self._config.timeout_seconds)
        received_content = False
        try:
            with client.stream(
                "POST",
                self._endpoint,
                headers=self._headers,
                json=self._payload(messages, stream=True),
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    line = line.strip()
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    content = payload["choices"][0].get("delta", {}).get("content")
                    if isinstance(content, str) and content:
                        received_content = True
                        yield content
            if not received_content:
                raise ValueError("empty stream")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise self._user_safe_error(exc) from exc
        finally:
            if owns_client:
                client.close()

    @property
    def _endpoint(self) -> str:
        return f"{self._config.base_url}/chat/completions"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

    def _payload(
        self, messages: Sequence[dict[str, str]], *, stream: bool
    ) -> dict[str, Any]:
        return {
            "model": self._config.model,
            "messages": list(messages),
            "temperature": 0.45,
            "max_tokens": 1000,
            "stream": stream,
        }

    def _ensure_configured(self) -> None:
        if not self._config.api_configured:
            raise DeepSeekError(
                "尚未配置 DeepSeek API Key。请填写 config.local.json 后重新启动应用。"
            )

    @staticmethod
    def _user_safe_error(exc: Exception) -> DeepSeekError:
        if isinstance(exc, httpx.TimeoutException):
            return DeepSeekError("DeepSeek 请求超时，请检查网络后重试。")
        if isinstance(exc, httpx.ConnectError):
            return DeepSeekError("无法连接 DeepSeek，请检查网络和 API 地址。")
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status in {401, 403}:
                return DeepSeekError("DeepSeek 拒绝了请求，请检查 API Key 是否正确。")
            if status == 429:
                return DeepSeekError("DeepSeek 请求过于频繁或额度不足，请稍后重试。")
            if status >= 500:
                return DeepSeekError("DeepSeek 服务暂时不可用，请稍后重试。")
            return DeepSeekError(f"DeepSeek 请求失败（HTTP {status}）。")
        return DeepSeekError("DeepSeek 返回了无法识别的数据。")

    @staticmethod
    def _extract_content(payload: Any) -> str:
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty content")
        return content.strip()
