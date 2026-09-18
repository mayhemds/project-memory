"""Tests for git activity collection."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from project_memory import git_activity
from project_memory.git_activity import (
    MAX_ACTIVITY_CHARS,
    collect_git_activity,
)


def test_non_git_directory_returns_explanatory_message(tmp_path: Path) -> None:
    result = collect_git_activity(tmp_path)

    assert "not a git repository" in result


def test_collects_log_and_diff_in_a_real_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial commit"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("changed", encoding="utf-8")

    result = collect_git_activity(tmp_path)

    assert "<<<GIT_ACTIVITY" in result
    assert "GIT_ACTIVITY>>>" in result
    assert "Uncommitted changes:" in result


def test_activity_is_wrapped_in_delimiters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(git_activity, "_run_git", lambda args, *, root: "abc123 commit")

    result = collect_git_activity(tmp_path)

    assert result.startswith("<<<GIT_ACTIVITY")
    assert result.rstrip().endswith("GIT_ACTIVITY>>>")
    assert "abc123 commit" in result


def test_empty_activity_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(git_activity, "_run_git", lambda args, *, root: "")

    result = collect_git_activity(tmp_path)

    assert "no recent git activity" in result


def test_git_failure_returns_explanatory_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()

    def boom(args: list[str], *, root: Path) -> str:
        raise git_activity.GitActivityError("git log failed: not a git repo")

    monkeypatch.setattr(git_activity, "_run_git", boom)

    result = collect_git_activity(tmp_path)

    assert "activity lookup failed" in result


def test_large_activity_is_truncated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(git_activity, "_run_git", lambda args, *, root: "x" * 50_000)

    result = collect_git_activity(tmp_path)

    assert "truncated" in result
    assert len(result) < MAX_ACTIVITY_CHARS + 100


def test_run_git_raises_on_missing_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(git_activity.GitActivityError, match="not installed"):
        git_activity._run_git(["log"], root=tmp_path)


def test_run_git_raises_on_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="git", timeout=1)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(git_activity.GitActivityError, match="timed out"):
        git_activity._run_git(["log"], root=tmp_path)


def test_run_git_raises_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(returncode=1, cmd="git", stderr="boom")

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(git_activity.GitActivityError, match="failed"):
        git_activity._run_git(["log"], root=tmp_path)
