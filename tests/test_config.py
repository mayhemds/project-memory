"""Tests for environment-driven configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_memory.config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    AISettings,
    registry_dir,
    registry_file,
)
from project_memory.exceptions import MemError


def test_registry_dir_honours_mem_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MEM_HOME", str(tmp_path / "custom"))

    assert registry_dir() == tmp_path / "custom"


def test_registry_file_lives_under_registry_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MEM_HOME", str(tmp_path))

    assert registry_file() == tmp_path / "projects.json"


def test_ai_settings_defaults_are_used_when_env_is_clear() -> None:
    settings = AISettings.from_env()

    assert settings.model == DEFAULT_MODEL
    assert settings.max_tokens == DEFAULT_MAX_TOKENS
    assert settings.timeout_seconds == DEFAULT_REQUEST_TIMEOUT_SECONDS
    assert settings.max_retries == DEFAULT_MAX_RETRIES


def test_ai_settings_read_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEM_MODEL", "claude-opus-5")
    monkeypatch.setenv("MEM_MAX_TOKENS", "512")
    monkeypatch.setenv("MEM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("MEM_MAX_RETRIES", "5")

    settings = AISettings.from_env()

    assert settings.model == "claude-opus-5"
    assert settings.max_tokens == 512
    assert settings.timeout_seconds == 12.5
    assert settings.max_retries == 5


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MEM_MAX_TOKENS", "not-a-number"),
        ("MEM_MAX_TOKENS", "0"),
        ("MEM_MAX_RETRIES", "-1"),
        ("MEM_TIMEOUT_SECONDS", "abc"),
        ("MEM_TIMEOUT_SECONDS", "0"),
    ],
)
def test_ai_settings_reject_invalid_overrides(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(MemError):
        AISettings.from_env()
