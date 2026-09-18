"""Runtime configuration, read from the environment with safe defaults.

Configuration is resolved lazily (at call time, not import time) so that tests
and commands can change the environment between operations. The one persistent
piece of state is the registry location, which lives under the user's config
directory unless ``MEM_HOME`` overrides it -- that override exists partly for
tests and partly so a user can keep their registry on a synced drive.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from .exceptions import MemError

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_MAX_TOKENS = 300
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2

_REGISTRY_DIR_NAME = "mem"
_REGISTRY_FILE_NAME = "projects.json"


def registry_dir() -> Path:
    """Return the directory that holds the global project registry.

    Honours the ``MEM_HOME`` environment variable when set, otherwise falls
    back to the platform's per-user config directory (for example
    ``~/.config/mem`` on Linux or ``~/Library/Application Support/mem`` on
    macOS).
    """
    override = os.environ.get("MEM_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    return user_config_path(_REGISTRY_DIR_NAME)


def registry_file() -> Path:
    """Return the path to the global project registry JSON file."""
    return registry_dir() / _REGISTRY_FILE_NAME


def _env_int(name: str, default: int, *, minimum: int) -> int:
    """Read a positive integer from the environment, falling back to `default`.

    Args:
        name: Environment variable name.
        default: Value to use when the variable is unset or blank.
        minimum: Smallest value that is considered valid.

    Raises:
        MemError: If the variable is set but not an integer, or is below
            `minimum`.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise MemError(f"{name} must be an integer, got {raw!r}.") from exc
    if value < minimum:
        raise MemError(f"{name} must be at least {minimum}, got {value}.")
    return value


def _env_float(name: str, default: float, *, minimum: float) -> float:
    """Read a positive float from the environment, falling back to `default`.

    Args:
        name: Environment variable name.
        default: Value to use when the variable is unset or blank.
        minimum: Smallest value that is considered valid.

    Raises:
        MemError: If the variable is set but not a number, or is below
            `minimum`.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise MemError(f"{name} must be a number, got {raw!r}.") from exc
    if value < minimum:
        raise MemError(f"{name} must be at least {minimum}, got {value}.")
    return value


@dataclass(frozen=True)
class AISettings:
    """Configuration for the optional ``mem save --ai`` drafting feature."""

    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES

    @classmethod
    def from_env(cls) -> AISettings:
        """Build settings from environment variables, falling back to defaults.

        ``ANTHROPIC_API_KEY`` is intentionally not read here; the Anthropic SDK
        reads it directly, so the key never passes through this module.

        Raises:
            MemError: If any ``MEM_*`` override is set but invalid.
        """
        model = os.environ.get("MEM_MODEL", "").strip() or DEFAULT_MODEL
        return cls(
            model=model,
            max_tokens=_env_int("MEM_MAX_TOKENS", DEFAULT_MAX_TOKENS, minimum=1),
            timeout_seconds=_env_float(
                "MEM_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT_SECONDS, minimum=0.1
            ),
            max_retries=_env_int("MEM_MAX_RETRIES", DEFAULT_MAX_RETRIES, minimum=0),
        )
