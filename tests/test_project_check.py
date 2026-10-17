"""Tests for the pre-init sanity checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_memory.project_check import has_project_marker, init_warnings


def _make_project(directory: Path) -> Path:
    directory.mkdir(parents=True)
    (directory / "package.json").write_text("{}", encoding="utf-8")
    return directory


def test_folder_with_marker_file_has_no_warnings(tmp_path: Path) -> None:
    project = _make_project(tmp_path / "app")

    assert init_warnings(project) == []


def test_git_folder_counts_as_a_marker(tmp_path: Path) -> None:
    project = tmp_path / "app"
    (project / ".git").mkdir(parents=True)

    assert has_project_marker(project)
    assert init_warnings(project) == []


def test_glob_markers_such_as_sln_are_recognised(tmp_path: Path) -> None:
    project = tmp_path / "dotnet-app"
    project.mkdir()
    (project / "App.sln").write_text("", encoding="utf-8")

    assert has_project_marker(project)


def test_empty_folder_warns_it_is_not_a_project(tmp_path: Path) -> None:
    folder = tmp_path / "scratch"
    folder.mkdir()

    warnings = init_warnings(folder)

    assert len(warnings) == 1
    assert "does not look like a project" in warnings[0]


def test_container_folder_names_the_projects_inside_it(tmp_path: Path) -> None:
    container = tmp_path / "client-a"
    for name in ("web", "api", "worker", "docs"):
        _make_project(container / name)

    warnings = init_warnings(container)

    assert len(warnings) == 1
    assert "4 folder(s) that look like projects" in warnings[0]
    assert "and 1 more" in warnings[0]
    assert "inside one of those" in warnings[0]


def test_home_folder_is_flagged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    warnings = init_warnings(tmp_path)

    assert any("home or filesystem root" in warning for warning in warnings)


def test_filesystem_root_is_flagged() -> None:
    assert any("home or filesystem root" in warning for warning in init_warnings(Path("/")))


def test_nested_inside_a_tracked_parent_is_flagged(tmp_path: Path) -> None:
    parent = _make_project(tmp_path / "parent")
    (parent / ".memory").mkdir()
    child = _make_project(parent / "child")

    warnings = init_warnings(child)

    assert len(warnings) == 1
    assert "already tracked" in warnings[0]
