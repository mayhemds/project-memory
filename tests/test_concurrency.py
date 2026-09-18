"""Regression tests for concurrent writers.

These reproduce the original lost-update bug: without a lock around the whole
read-modify-write cycle, parallel ``mem`` invocations could each read the same
registry and then clobber one another, silently dropping entries. Real
processes are used deliberately -- threads would not exercise the same file
locking behaviour, and the point is to prove the fix works across processes.
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path

import pytest

from project_memory.config import registry_file
from project_memory.registry import load_registry, upsert_project
from project_memory.statefile import append_session_entry, initialize_project

pytestmark = pytest.mark.integration


def _upsert_worker(name: str, path: str, timestamp: str) -> None:
    """Top-level worker so it is picklable by multiprocessing on all platforms."""
    upsert_project(name, Path(path), timestamp)


def _append_worker(root: str, note: str, timestamp: str) -> None:
    """Top-level worker that appends one session entry."""
    append_session_entry(Path(root), note, timestamp)


def test_concurrent_upserts_do_not_lose_entries() -> None:
    processes = [
        multiprocessing.Process(
            target=_upsert_worker,
            args=(f"project-{index}", f"/tmp/project-{index}", "2026-09-18T10:00"),
        )
        for index in range(8)
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
        assert process.exitcode == 0

    names = {project.name for project in load_registry()}
    assert names == {f"project-{index}" for index in range(8)}


def test_concurrent_session_appends_are_all_preserved(project_dir: Path) -> None:
    initialize_project(project_dir, "2026-09-18T10:00")
    processes = [
        multiprocessing.Process(
            target=_append_worker, args=(str(project_dir), f"note-{index}", "2026-09-18T10:00")
        )
        for index in range(6)
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
        assert process.exitcode == 0

    content = (project_dir / ".memory" / "STATE.md").read_text(encoding="utf-8")
    for index in range(6):
        assert content.count(f"- note-{index}") == 1


def test_registry_is_valid_json_and_parseable_after_concurrent_writes() -> None:
    processes = [
        multiprocessing.Process(
            target=_upsert_worker,
            args=(f"p{index}", f"/tmp/p{index}", "2026-09-18T10:00"),
        )
        for index in range(6)
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)

    assert registry_file().exists()
    assert len(load_registry()) == 6
