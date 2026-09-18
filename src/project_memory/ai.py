"""Optional AI drafting of session entries from git activity.

This module is the only place the Anthropic SDK is touched. Design choices
worth noting:

* The API key is never read into this process explicitly; the SDK reads
  ``ANTHROPIC_API_KEY`` from the environment itself, so the secret never
  passes through our code or our logs.
* The system prompt and the untrusted git activity are separated at the
  message-role level, and the activity is additionally wrapped in delimiters
  by :mod:`project_memory.git_activity`, so injected text inside a commit
  message is framed as data.
* Calls carry an explicit timeout, a bounded retry count, and a ``max_tokens``
  cap, so a hung or misbehaving API cannot block the CLI indefinitely or run
  away on cost.
"""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path

from .config import AISettings
from .exceptions import AIError

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_ENTRY_MAX_CHARS = 2000


@cache
def _load_prompt(name: str) -> str:
    """Load a prompt template from the packaged ``prompts`` directory.

    Prompts live in files rather than inline strings so they are reviewable,
    diffable, and testable on their own.

    Raises:
        AIError: If the template file is missing.
    """
    path = _PROMPTS_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AIError(f"Prompt template {name!r} is missing: {exc}") from exc


def _build_user_prompt(activity: str) -> str:
    """Render the user-message prompt with the delimited git activity."""
    template = _load_prompt("draft_entry.txt")
    return template.replace("{{ activity }}", activity)


def draft_entry_with_ai(activity: str, *, settings: AISettings | None = None) -> str:
    """Ask Claude to draft a session log entry from raw git activity.

    Args:
        activity: Delimited git activity text, as produced by
            :func:`project_memory.git_activity.collect_git_activity`.
        settings: Optional configuration override, mainly for tests. When
            omitted, settings are read from the environment.

    Returns:
        The drafted entry as plain text, or ``"(no draft produced)"`` if the
        model returned no text.

    Raises:
        AIError: If the ``anthropic`` package is missing, the API key is
            unset, or the API call fails.
    """
    resolved = settings if settings is not None else AISettings.from_env()

    try:
        import anthropic
    except ImportError as exc:
        raise AIError(
            "The --ai flag needs the anthropic package. Install it with: uv add anthropic"
        ) from exc

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AIError("The --ai flag needs an ANTHROPIC_API_KEY environment variable to be set.")

    client = anthropic.Anthropic(
        timeout=resolved.timeout_seconds,
        max_retries=resolved.max_retries,
    )
    system_prompt = _load_prompt("draft_entry_system.txt").strip()

    try:
        response = client.messages.create(
            model=resolved.model,
            max_tokens=resolved.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": _build_user_prompt(activity)}],
        )
    except anthropic.APIError as exc:
        raise AIError(f"Claude API call failed: {exc}") from exc

    text_blocks: list[str] = [
        str(getattr(block, "text", ""))
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]
    text = "".join(text_blocks).strip()
    if not text:
        return "(no draft produced)"
    return text[:_ENTRY_MAX_CHARS]
