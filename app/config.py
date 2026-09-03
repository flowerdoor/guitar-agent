from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    """Raised when the local configuration cannot be read safely."""


@dataclass(frozen=True)
class AppConfig:
    api_key: str = field(default="", repr=False)
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout_seconds: float = 45.0

    @property
    def api_configured(self) -> bool:
        return bool(self.api_key.strip())


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()

    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"无法读取配置文件 {path.name}：{exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"配置文件 {path.name} 的顶层内容必须是 JSON 对象。")

    try:
        timeout = float(raw.get("timeout_seconds", 45))
    except (TypeError, ValueError) as exc:
        raise ConfigError("timeout_seconds 必须是数字。") from exc
    if not 5 <= timeout <= 180:
        raise ConfigError("timeout_seconds 必须在 5 到 180 秒之间。")

    base_url = str(raw.get("base_url", "https://api.deepseek.com")).strip().rstrip("/")
    if not base_url.startswith(("https://", "http://")):
        raise ConfigError("base_url 必须以 http:// 或 https:// 开头。")

    model = str(raw.get("model", "deepseek-chat")).strip()
    if not model:
        raise ConfigError("model 不能为空。")

    return AppConfig(
        api_key=str(raw.get("api_key", "")).strip(),
        base_url=base_url,
        model=model,
        timeout_seconds=timeout,
    )

