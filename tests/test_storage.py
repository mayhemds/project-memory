"""Tests for atomic writes, locking, and JSON loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_memory.exceptions import RegistryError, StorageError
from project_memory.storage import (
    atomic_write_text,
    file_lock,
    load_json,
)


def test_atomic_write_creates_file_and_parents(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deep" / "state.md"

    atomic_write_text(target, "hello\n")

    assert target.read_text(encoding="utf-8") == "hello\n"


def test_atomic_write_replaces_existing_content(tmp_path: Path) -> None:
    target = tmp_path / "state.md"
    target.write_text("old", encoding="utf-8")

    atomic_write_text(target, "new")

    assert target.read_text(encoding="utf-8") == "new"


def test_atomic_write_leaves_no_temp_files_behind(tmp_path: Path) -> None:
    target = tmp_path / "state.md"

    atomic_write_text(target, "content")

    leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


def test_atomic_write_raises_storage_error_when_not_writable(tmp_path: Path) -> None:
    target = tmp_path / "adir"
    target.mkdir()

    with pytest.raises(StorageError):
        atomic_write_text(target, "content")


def test_file_lock_is_reentrant_across_sequential_uses(tmp_path: Path) -> None:
    target = tmp_path / "registry.json"

    with file_lock(target):
        target.write_text("first", encoding="utf-8")
    with file_lock(target):
        target.write_text("second", encoding="utf-8")

    assert target.read_text(encoding="utf-8") == "second"


def test_file_lock_releases_after_exception(tmp_path: Path) -> None:
    target = tmp_path / "registry.json"

    with pytest.raises(RuntimeError), file_lock(target):
        raise RuntimeError("boom")

    with file_lock(target):
        target.write_text("ok", encoding="utf-8")
    assert target.read_text(encoding="utf-8") == "ok"


def test_load_json_decodes_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text(json.dumps([{"a": 1}]), encoding="utf-8")

    assert load_json(path, source_label="Data") == [{"a": 1}]


def test_load_json_rejects_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RegistryError, match="corrupted"):
        load_json(path, source_label="Registry file")


def test_load_json_raises_storage_error_for_unreadable_file(tmp_path: Path) -> None:
    directory = tmp_path / "not-a-file"
    directory.mkdir()

    with pytest.raises(StorageError):
        load_json(directory, source_label="Registry file")
