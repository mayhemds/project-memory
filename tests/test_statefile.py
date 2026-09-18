"""Tests for state file creation, reading, and session appends."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_memory.exceptions import ProjectNotInitializedError, StateFileError
from project_memory.statefile import (
    STATE_DIR_NAME,
    append_session_entry,
    find_project_root,
    initialize_project,
    read_state,
    state_file,
)


def test_initialize_project_creates_state_file(project_dir: Path) -> None:
    path = initialize_project(project_dir, "2026-09-18T10:30")

    assert path == project_dir / STATE_DIR_NAME / "STATE.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "project: my-project" in content
    assert "last_updated: 2026-09-18T10:30" in content
    assert "## Session log" in content


def test_initialize_project_rejects_double_init(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")

    with pytest.raises(StateFileError, match="already tracked"):
        initialize_project(project_dir, "2026-09-18T10:31")


def test_read_state_returns_file_contents(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")

    assert "## Current focus" in read_state(project_dir)


def test_read_state_raises_when_not_initialized(project_dir: Path) -> None:
    with pytest.raises(ProjectNotInitializedError, match="mem init"):
        read_state(project_dir)


def test_find_project_root_finds_nearest_initialized_ancestor(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")
    nested = project_dir / "src" / "deep"
    nested.mkdir(parents=True)

    assert find_project_root(nested) == project_dir.resolve()


def test_find_project_root_falls_back_to_start(tmp_path: Path) -> None:
    lonely = tmp_path / "nowhere"
    lonely.mkdir()

    assert find_project_root(lonely) == lonely.resolve()


def test_append_session_entry_adds_entry_and_updates_timestamp(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")

    append_session_entry(project_dir, "fixed the auth bug", "2026-09-18T14:00")

    content = read_state(project_dir)
    assert "### 2026-09-18T14:00" in content
    assert "- fixed the auth bug" in content
    assert "last_updated: 2026-09-18T14:00" in content


def test_append_session_entry_preserves_trailing_newline(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")

    append_session_entry(project_dir, "note", "2026-09-18T14:00")

    assert read_state(project_dir).endswith("\n")


def test_append_session_entry_is_idempotent_per_call(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:30")

    append_session_entry(project_dir, "first", "2026-09-18T14:00")
    append_session_entry(project_dir, "second", "2026-09-18T15:00")

    content = read_state(project_dir)
    assert content.count("- first") == 1
    assert content.count("- second") == 1


def test_append_session_entry_raises_when_not_initialized(project_dir: Path) -> None:
    with pytest.raises(ProjectNotInitializedError):
        append_session_entry(project_dir, "note", "2026-09-18T14:00")


def test_append_session_entry_rejects_file_without_frontmatter(project_dir: Path) -> None:
    path = state_file(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Just a heading\n", encoding="utf-8")

    with pytest.raises(StateFileError, match="frontmatter"):
        append_session_entry(project_dir, "note", "2026-09-18T14:00")


def test_append_session_entry_rejects_unclosed_frontmatter(project_dir: Path) -> None:
    path = state_file(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nproject: x\nlast_updated: 2026-09-18T10:30\n", encoding="utf-8")

    with pytest.raises(StateFileError, match="not closed"):
        append_session_entry(project_dir, "note", "2026-09-18T14:00")


def test_append_session_entry_rejects_missing_timestamp_field(project_dir: Path) -> None:
    path = state_file(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nproject: x\n---\n", encoding="utf-8")

    with pytest.raises(StateFileError, match="last_updated"):
        append_session_entry(project_dir, "note", "2026-09-18T14:00")
