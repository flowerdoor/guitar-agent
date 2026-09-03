import json

import pytest

from app.config import ConfigError, load_config


def test_missing_config_starts_without_api_key(tmp_path):
    config = load_config(tmp_path / "missing.json")

    assert config.api_configured is False
    assert config.model == "deepseek-chat"


def test_config_loads_values_without_exposing_key_in_repr(tmp_path):
    path = tmp_path / "config.local.json"
    path.write_text(
        json.dumps(
            {
                "api_key": "secret-value",
                "base_url": "https://example.test/",
                "model": "test-model",
                "timeout_seconds": 30,
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.api_key == "secret-value"
    assert config.base_url == "https://example.test"
    assert "secret-value" not in repr(config)


@pytest.mark.parametrize(
    "content, expected",
    [
        ("[]", "顶层内容"),
        ('{"timeout_seconds": 2}', "5 到 180"),
        ('{"base_url": "ftp://example.com"}', "http://"),
    ],
)
def test_invalid_config_is_rejected(tmp_path, content, expected):
    path = tmp_path / "config.local.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigError, match=expected):
        load_config(path)

