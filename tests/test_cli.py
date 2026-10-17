"""End-to-end tests for the ``mem`` CLI.

These exercise the real command wiring through :func:`main`, not the command
functions in isolation, so argument parsing, error handling, and exit codes are
covered alongside the logic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from project_memory import cli
from project_memory.config import registry_file
from project_memory.statefile import state_file


def _run(argv: list[str]) -> int:
    """Invoke the CLI and translate its exit behaviour into a return code."""
    try:
        cli.main(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def test_init_creates_state_file_and_registry(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(["init"]) == 0

    assert state_file(project_dir).exists()
    assert registry_file().exists()
    assert "Initialized project memory" in capsys.readouterr().out


def test_init_twice_reports_error(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])

    assert _run(["init"]) == 1
    assert "already tracked" in capsys.readouterr().err


def test_save_with_inline_note(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])

    assert _run(["save", "fixed the bug"]) == 0

    content = state_file(project_dir).read_text(encoding="utf-8")
    assert "- fixed the bug" in content
    assert "Saved to" in capsys.readouterr().out


def test_save_prompts_when_no_note_given(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _run(["init"])
    monkeypatch.setattr("builtins.input", lambda *_: "typed note")

    _run(["save"])

    assert "- typed note" in state_file(project_dir).read_text(encoding="utf-8")


def test_save_rejects_empty_interactive_note(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    monkeypatch.setattr("builtins.input", lambda *_: "   ")

    assert _run(["save"]) == 1
    assert "No note provided" in capsys.readouterr().err


def test_save_requires_initialized_project(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["save", "note"]) == 1
    assert "mem init" in capsys.readouterr().err


def test_save_rejects_note_and_ai_together(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])

    assert _run(["save", "note", "--ai"]) == 1
    assert "not both" in capsys.readouterr().err


def test_save_ai_discards_on_no(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    monkeypatch.setattr(cli, "collect_git_activity", lambda root: "activity")
    monkeypatch.setattr(cli, "draft_entry_with_ai", lambda activity: "drafted")
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    assert _run(["save", "--ai"]) == 0

    assert "- drafted" not in state_file(project_dir).read_text(encoding="utf-8")
    assert "Discarded" in capsys.readouterr().out


def test_save_ai_saves_on_yes(project_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run(["init"])
    monkeypatch.setattr(cli, "collect_git_activity", lambda root: "activity")
    monkeypatch.setattr(cli, "draft_entry_with_ai", lambda activity: "drafted entry")
    monkeypatch.setattr("builtins.input", lambda *_: "y")

    _run(["save", "--ai"])

    assert "- drafted entry" in state_file(project_dir).read_text(encoding="utf-8")


def test_save_ai_edit_replaces_entry(project_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run(["init"])
    monkeypatch.setattr(cli, "collect_git_activity", lambda root: "activity")
    monkeypatch.setattr(cli, "draft_entry_with_ai", lambda activity: "drafted")
    responses = iter(["edit", "my own line", ""])
    monkeypatch.setattr("builtins.input", lambda *_: next(responses))

    _run(["save", "--ai"])

    content = state_file(project_dir).read_text(encoding="utf-8")
    assert "- my own line" in content
    assert "- drafted" not in content


def test_status_prints_state_file(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])
    capsys.readouterr()

    assert _run(["status"]) == 0
    assert "## Current focus" in capsys.readouterr().out


def test_status_requires_initialized_project(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["status"]) == 1
    assert "mem init" in capsys.readouterr().err


def test_list_shows_tracked_projects(
    project_dir: Path, isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    capsys.readouterr()

    assert _run(["list"]) == 0
    assert "my-project" in capsys.readouterr().out


def test_list_errors_when_registry_empty(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["list"]) == 1
    assert "No projects tracked" in capsys.readouterr().err


def test_last_prints_most_recent_state(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    capsys.readouterr()

    assert _run(["last"]) == 0
    out = capsys.readouterr().out
    assert "Most recent project: my-project" in out
    assert "## Current focus" in out


def test_last_since_lists_recent_projects(
    project_dir: Path, isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    capsys.readouterr()

    assert _run(["last", "--since", "7d"]) == 0
    assert "my-project" in capsys.readouterr().out


def test_last_since_rejects_bad_duration(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])

    assert _run(["last", "--since", "banana"]) == 1
    assert "Invalid duration" in capsys.readouterr().err


def test_search_finds_matching_lines(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])
    _run(["save", "fix the login bug"])
    capsys.readouterr()

    assert _run(["search", "login"]) == 0
    assert "login bug" in capsys.readouterr().out


def test_search_is_case_insensitive(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])
    _run(["save", "Fix the Login Bug"])
    capsys.readouterr()

    _run(["search", "LOGIN"])

    assert "Login Bug" in capsys.readouterr().out


def test_search_reports_no_matches(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["init"])
    capsys.readouterr()

    assert _run(["search", "zzzznothing"]) == 0
    assert "No matches" in capsys.readouterr().out


def test_search_treats_keyword_as_literal(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    _run(["save", "ordinary note"])
    capsys.readouterr()

    assert _run(["search", "'; DROP TABLE projects; --"]) == 0
    assert "No matches" in capsys.readouterr().out


def test_sync_merges_registries(
    project_dir: Path, isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    shared = isolated_env / "shared.json"
    shared.write_text(
        json.dumps([{"name": "other", "path": "/tmp/other", "last_updated": "2020-01-01T00:00"}]),
        encoding="utf-8",
    )
    capsys.readouterr()

    assert _run(["sync", str(shared)]) == 0
    assert "Synced 2 project(s)" in capsys.readouterr().out


def test_unknown_command_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["frobnicate"])

    assert exc.value.code != 0


def test_missing_command_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code != 0


def test_save_keeps_multiline_note_in_one_bullet(project_dir: Path) -> None:
    _run(["init"])

    assert _run(["save", "first line\n## Sneaky heading"]) == 0

    text = state_file(project_dir).read_text(encoding="utf-8")
    assert "- first line\n  ## Sneaky heading\n" in text


def test_registry_timestamps_are_written_in_utc(project_dir: Path) -> None:
    _run(["init"])

    stored = json.loads(registry_file().read_text(encoding="utf-8"))

    assert stored[0]["last_updated"].endswith("Z")


def test_init_rolls_back_when_registry_cannot_be_updated(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from project_memory.exceptions import StorageError

    def fail(*args: object, **kwargs: object) -> None:
        raise StorageError("disk full")

    with monkeypatch.context() as patch:
        patch.setattr(cli, "upsert_project", fail)

        assert _run(["init"]) == 1

    assert "disk full" in capsys.readouterr().err
    assert not (project_dir / ".memory").exists()
    assert _run(["init"]) == 0


def _write_foreign_entry(isolated_env: Path) -> Path:
    shared = isolated_env / "shared.json"
    shared.write_text(
        json.dumps(
            [
                {
                    "name": "alice-app",
                    "path": "/Users/alice/alice-app",
                    "last_updated": "2999-01-01T00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    return shared


def test_synced_foreign_projects_do_not_hijack_last(
    project_dir: Path, isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    _run(["sync", str(_write_foreign_entry(isolated_env))])
    capsys.readouterr()

    assert _run(["last"]) == 0
    captured = capsys.readouterr()
    assert "Most recent project: my-project" in captured.out
    assert "alice-app" not in captured.out
    assert "1 tracked project(s) not found on this machine" in captured.err


def test_synced_foreign_projects_are_hidden_from_list_and_since(
    project_dir: Path, isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["init"])
    _run(["sync", str(_write_foreign_entry(isolated_env))])
    capsys.readouterr()

    assert _run(["list"]) == 0
    assert "alice-app" not in capsys.readouterr().out
    assert _run(["last", "--since", "7d"]) == 0
    assert "alice-app" not in capsys.readouterr().out


def test_last_errors_when_nothing_tracked_exists_locally(
    isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["sync", str(_write_foreign_entry(isolated_env))])
    capsys.readouterr()

    assert _run(["last"]) == 1
    assert "exist on this machine" in capsys.readouterr().err


def test_init_warns_and_cancels_in_a_non_project_folder(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = isolated_env / "projects-folder"
    folder.mkdir()
    os.chdir(folder)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    assert _run(["init"]) == 1

    captured = capsys.readouterr()
    assert "does not look like a project" in captured.err
    assert "Nothing was created" in captured.err
    assert not (folder / ".memory").exists()
    assert not registry_file().exists()


def test_init_proceeds_when_the_warning_is_confirmed(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = isolated_env / "scratch"
    folder.mkdir()
    os.chdir(folder)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")

    assert _run(["init"]) == 0
    assert (folder / ".memory" / "STATE.md").exists()


def test_init_yes_flag_skips_the_warning(
    isolated_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = isolated_env / "scratch"
    folder.mkdir()
    os.chdir(folder)

    assert _run(["init", "--yes"]) == 0
    assert "Warning" not in capsys.readouterr().err


def test_init_without_input_fails_instead_of_guessing(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = isolated_env / "scratch"
    folder.mkdir()
    os.chdir(folder)

    def no_input(_prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)

    assert _run(["init"]) == 1
    assert "--yes" in capsys.readouterr().err
    assert not (folder / ".memory").exists()


def test_init_in_a_real_project_does_not_prompt(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(["init"]) == 0
    assert "Warning" not in capsys.readouterr().err
