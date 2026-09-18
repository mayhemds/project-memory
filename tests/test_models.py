"""Tests for registry model validation and parsing."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from project_memory.exceptions import RegistryError
from project_memory.models import Project, parse_projects


def test_project_accepts_valid_entry() -> None:
    project = Project(name="api", path="/tmp/api", last_updated="2026-09-18T10:30")

    assert project.name == "api"
    assert project.resolved_path == Path("/tmp/api")


def test_project_ignores_unknown_keys() -> None:
    project = Project.model_validate(
        {
            "name": "api",
            "path": "/tmp/api",
            "last_updated": "2026-09-18T10:30",
            "future_field": "ignored",
        }
    )

    assert project.name == "api"


@pytest.mark.parametrize(
    "entry",
    [
        {"name": "api", "path": "/tmp/api"},
        {"name": "api", "last_updated": "2026-09-18T10:30"},
        {"path": "/tmp/api", "last_updated": "2026-09-18T10:30"},
        {"name": "", "path": "/tmp/api", "last_updated": "2026-09-18T10:30"},
        {"name": 1, "path": "/tmp/api", "last_updated": "2026-09-18T10:30"},
    ],
)
def test_project_rejects_missing_or_wrongly_typed_fields(entry: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Project.model_validate(entry)


@pytest.mark.parametrize(
    "timestamp",
    ["2026-9-18T10:30", "2026-09-18 10:30", "2026-09-18T10:30:00", "yesterday", "2026-13-01T00:00"],
)
def test_project_rejects_malformed_timestamps(timestamp: str) -> None:
    with pytest.raises(ValidationError):
        Project(name="api", path="/tmp/api", last_updated=timestamp)


def test_parse_projects_returns_validated_entries() -> None:
    raw = [{"name": "api", "path": "/tmp/api", "last_updated": "2026-09-18T10:30"}]

    projects = parse_projects(raw, source=Path("registry.json"))

    assert len(projects) == 1
    assert projects[0].name == "api"


def test_parse_projects_rejects_non_list() -> None:
    with pytest.raises(RegistryError, match="JSON list"):
        parse_projects({"name": "api"}, source=Path("registry.json"))


def test_parse_projects_rejects_malformed_entry() -> None:
    with pytest.raises(RegistryError, match="malformed entry"):
        parse_projects([{"name": "api"}], source=Path("registry.json"))


def test_parse_projects_rejects_entry_of_wrong_type() -> None:
    with pytest.raises(RegistryError):
        parse_projects(["not-an-object"], source=Path("registry.json"))
