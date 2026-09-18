"""Shared test fixtures.

Every test runs against a throwaway ``MEM_HOME`` and a throwaway working
directory, so no test can read or write the developer's real registry, real
projects, or real ``.memory`` files. The environment is reset between tests so
tests are independent and order-insensitive.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point MEM_HOME at a temp dir and run the test inside a temp cwd.

    Yields:
        The isolated home directory, which is also ``tmp_path`` so tests can
        create sibling directories for fake projects.
    """
    home = tmp_path / "mem-home"
    home.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("MEM_HOME", str(home))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MEM_MODEL", raising=False)
    monkeypatch.delenv("MEM_MAX_TOKENS", raising=False)
    monkeypatch.delenv("MEM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("MEM_MAX_RETRIES", raising=False)
    monkeypatch.chdir(work)
    yield tmp_path


@pytest.fixture
def project_dir(isolated_env: Path) -> Path:
    """Create an empty candidate project directory and chdir into it."""
    directory = isolated_env / "my-project"
    directory.mkdir()
    os.chdir(directory)
    return directory
