"""Tests for the global project registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_memory.config import registry_file
from project_memory.exceptions import RegistryError
from project_memory.models import Project
from project_memory.registry import (
    load_registry,
    load_shared_registry,
    merge_projects,
    save_registry,
    sync_with_shared,
    upsert_project,
)


def test_load_registry_returns_empty_when_absent() -> None:
    assert load_registry() == []


def test_upsert_project_adds_new_entry() -> None:
    upsert_project("api", Path("/tmp/api"), "2026-09-18T10:30")

    projects = load_registry()
    assert len(projects) == 1
    assert projects[0].name == "api"
    assert projects[0].path == str(Path("/tmp/api").resolve())


def test_upsert_project_updates_existing_entry_without_duplicating() -> None:
    upsert_project("api", Path("/tmp/api"), "2026-09-18T10:30")
    upsert_project("api-renamed", Path("/tmp/api"), "2026-09-18T11:00")

    projects = load_registry()
    assert len(projects) == 1
    assert projects[0].name == "api-renamed"
    assert projects[0].last_updated == "2026-09-18T11:00"


def test_upsert_project_resolves_relative_paths() -> None:
    upsert_project("here", Path("."), "2026-09-18T10:30")

    stored = load_registry()[0]
    assert stored.path == str(Path.cwd().resolve())


def test_upsert_project_accumulates_multiple_projects() -> None:
    upsert_project("one", Path("/tmp/one"), "2026-09-18T10:00")
    upsert_project("two", Path("/tmp/two"), "2026-09-18T11:00")

    assert {p.name for p in load_registry()} == {"one", "two"}


def test_load_registry_rejects_corrupt_json() -> None:
    registry_file().parent.mkdir(parents=True, exist_ok=True)
    registry_file().write_text("{not json", encoding="utf-8")

    with pytest.raises(RegistryError, match="corrupted"):
        load_registry()


def test_save_registry_writes_valid_json() -> None:
    save_registry([Project(name="api", path="/tmp/api", last_updated="2026-09-18T10:30")])

    raw = json.loads(registry_file().read_text(encoding="utf-8"))
    assert raw == [{"name": "api", "path": "/tmp/api", "last_updated": "2026-09-18T10:30"}]


def test_merge_prefers_more_recent_entry() -> None:
    shared = [Project(name="old", path="/p", last_updated="2026-09-18T10:00")]
    local = [Project(name="new", path="/p", last_updated="2026-09-18T12:00")]

    merged = merge_projects(shared, local)

    assert len(merged) == 1
    assert merged[0].name == "new"


def test_merge_is_order_independent_on_ties() -> None:
    a = [Project(name="a", path="/p", last_updated="2026-09-18T10:00")]
    b = [Project(name="b", path="/p", last_updated="2026-09-18T10:00")]

    assert merge_projects(a, b) == merge_projects(b, a)


def test_load_shared_registry_returns_empty_when_missing(tmp_path: Path) -> None:
    assert load_shared_registry(tmp_path / "missing.json") == []


def test_sync_writes_identical_content_to_both_files(tmp_path: Path) -> None:
    upsert_project("local-only", Path("/tmp/local"), "2026-09-18T12:00")
    shared = tmp_path / "shared.json"
    shared.write_text(
        json.dumps(
            [
                {
                    "name": "shared-only",
                    "path": "/tmp/shared",
                    "last_updated": "2026-09-18T11:00",
                }
            ]
        ),
        encoding="utf-8",
    )

    count = sync_with_shared(shared)

    assert count == 2
    local_data = json.loads(registry_file().read_text(encoding="utf-8"))
    shared_data = json.loads(shared.read_text(encoding="utf-8"))
    assert local_data == shared_data
    assert {entry["name"] for entry in local_data} == {"local-only", "shared-only"}


def test_sync_creates_shared_file_when_absent(tmp_path: Path) -> None:
    upsert_project("only", Path("/tmp/only"), "2026-09-18T12:00")
    shared = tmp_path / "new" / "shared.json"

    sync_with_shared(shared)

    assert shared.exists()
    assert load_shared_registry(shared)[0].name == "only"


def test_sync_rejects_corrupt_shared_file(tmp_path: Path) -> None:
    shared = tmp_path / "shared.json"
    shared.write_text("not json", encoding="utf-8")

    with pytest.raises(RegistryError):
        sync_with_shared(shared)
