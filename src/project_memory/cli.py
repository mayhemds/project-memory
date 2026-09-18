"""The ``mem`` command-line interface.

Each ``cmd_*`` function is a thin orchestration layer: it reads arguments,
calls into the storage/registry/ai modules, and prints results. All expected
failures are raised as :class:`~project_memory.exceptions.MemError` subclasses
and rendered cleanly by :func:`main`; unexpected exceptions are caught by a
last-resort handler so a user never sees a raw traceback.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from .ai import draft_entry_with_ai
from .durations import parse_duration
from .exceptions import MemError
from .git_activity import collect_git_activity
from .models import TIMESTAMP_FORMAT, Project
from .registry import load_registry, sync_with_shared, upsert_project
from .statefile import (
    append_session_entry,
    find_project_root,
    initialize_project,
    read_state,
    state_file,
)


def _now_iso() -> str:
    """Return the current local time as ``YYYY-MM-DDTHH:MM``."""
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def _require_registry() -> list[Project]:
    """Load the registry, raising a friendly error when it is empty."""
    projects = load_registry()
    if not projects:
        raise MemError("No projects tracked yet. Run 'mem init' inside a project first.")
    return projects


def _project_for_command() -> tuple[Path, Path]:
    """Resolve the current project root and its state file path.

    Returns:
        A ``(root, state_path)`` pair.
    """
    root = find_project_root(Path.cwd())
    return root, state_file(root)


def cmd_init(_: argparse.Namespace) -> None:
    """Create a ``.memory/STATE.md`` file in the current directory and register it."""
    root = Path.cwd()
    timestamp = _now_iso()
    path = initialize_project(root, timestamp)
    upsert_project(root.name, root, timestamp)
    print(f"Initialized project memory at {path}")


def _prompt_for_note() -> str:
    """Read a session note interactively, rejecting an empty entry.

    Raises:
        MemError: If the user enters nothing.
    """
    note = input("Session note: ").strip()
    if not note:
        raise MemError("No note provided. Pass one as an argument or type one when prompted.")
    return note


def _prompt_for_edited_entry(draft: str) -> str:
    """Let the user replace an AI draft with their own multi-line text.

    Reads lines until an empty line or EOF, then falls back to `draft` if the
    user submits nothing.
    """
    print("Enter your version (finish with an empty line):")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    edited = "\n".join(lines).strip()
    return edited or draft


def _resolve_ai_note(root: Path) -> str | None:
    """Draft an entry with AI and let the user confirm, edit, or discard it.

    Returns:
        The note to save, or ``None`` if the user discarded the draft.
    """
    activity = collect_git_activity(root)
    draft = draft_entry_with_ai(activity)
    print("--- Drafted entry ---")
    print(draft)
    print("---------------------")
    try:
        choice = input("Save this entry? [y/N/edit]: ").strip().lower()
    except EOFError:
        print("\nNo input available. Discarded. Nothing saved.")
        return None
    if choice == "edit":
        return _prompt_for_edited_entry(draft)
    if choice == "y":
        return draft
    print("Discarded. Nothing saved.")
    return None


def cmd_save(args: argparse.Namespace) -> None:
    """Append a session log entry to the current project's state file."""
    root, path = _project_for_command()
    if not path.exists():
        raise MemError(f"No memory file found at {path}. Run 'mem init' first.")

    if args.ai and args.note:
        raise MemError("Pass either a note or --ai, not both.")

    timestamp = _now_iso()

    if args.ai:
        note = _resolve_ai_note(root)
        if note is None:
            return
    else:
        note = args.note or _prompt_for_note()

    append_session_entry(root, note, timestamp)
    upsert_project(root.name, root, timestamp)
    print(f"Saved to {path}")


def cmd_status(_: argparse.Namespace) -> None:
    """Print the current project's state file to the terminal."""
    root = find_project_root(Path.cwd())
    print(read_state(root), end="")


def cmd_last(args: argparse.Namespace) -> None:
    """Show the most recently touched project, or all touched within a window.

    Without ``--since`` this is a single-project lookup: the most recently
    touched project in the registry, shown in full. With ``--since`` it lists
    every project touched within that window, most recent first, since at that
    point the user is scanning a period of work rather than resuming one
    session.
    """
    projects = _require_registry()

    if args.since is None:
        latest = max(projects, key=lambda project: project.last_updated)
        print(f"Most recent project: {latest.name} ({latest.path})")
        print(f"Last touched: {latest.last_updated}\n")
        latest_state = state_file(Path(latest.path))
        if latest_state.exists():
            print(latest_state.read_text(encoding="utf-8"), end="")
        else:
            print("(state file missing, registry may be stale)")
        return

    window = parse_duration(args.since)
    cutoff = datetime.now() - window
    recent = [
        project
        for project in projects
        if datetime.strptime(project.last_updated, TIMESTAMP_FORMAT) >= cutoff
    ]
    if not recent:
        print(f"No projects touched in the last {args.since}.")
        return
    for project in sorted(recent, key=lambda entry: entry.last_updated, reverse=True):
        print(f"{project.last_updated}  {project.name:<25}  {project.path}")


def cmd_list(_: argparse.Namespace) -> None:
    """List all tracked projects, most recently touched first."""
    for project in sorted(_require_registry(), key=lambda entry: entry.last_updated, reverse=True):
        print(f"{project.last_updated}  {project.name:<25}  {project.path}")


def cmd_search(args: argparse.Namespace) -> None:
    """Search every tracked project's state file for a keyword.

    Matching is case-insensitive and reported per line, so results carry
    enough context to be useful without opening each file.
    """
    projects = _require_registry()
    keyword = args.keyword.lower()
    found_any = False
    for project in sorted(projects, key=lambda entry: entry.last_updated, reverse=True):
        path = state_file(Path(project.path))
        if not path.exists():
            continue
        matches = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if keyword in line.lower()
        ]
        if matches:
            found_any = True
            print(f"\n{project.name} ({project.path})")
            for line in matches:
                print(f"  {line}")

    if not found_any:
        print(f"No matches for {args.keyword!r} in any tracked project.")


def cmd_sync(args: argparse.Namespace) -> None:
    """Merge the local registry with a shared registry file.

    Shared file paths may point anywhere the user can read and write: a synced
    folder, a shared drive, or a git-tracked path. The merge keeps whichever
    entry per project is more recent and writes both copies back, so repeated
    runs converge.
    """
    shared_path = Path(args.shared_path).expanduser()
    count = sync_with_shared(shared_path)
    print(f"Synced {count} project(s) with {shared_path}")


def build_parser() -> argparse.ArgumentParser:
    """Construct the ``mem`` argument parser."""
    parser = argparse.ArgumentParser(prog="mem", description="Cross-project session memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "init", help="Register the current directory as a tracked project."
    ).set_defaults(func=cmd_init)

    save_parser = subparsers.add_parser("save", help="Record a session entry.")
    save_parser.add_argument("note", nargs="?", default=None, help="The note to save.")
    save_parser.add_argument(
        "--ai", action="store_true", help="Draft the entry from git activity using Claude."
    )
    save_parser.set_defaults(func=cmd_save)

    subparsers.add_parser("status", help="Show the current project's state file.").set_defaults(
        func=cmd_status
    )

    last_parser = subparsers.add_parser("last", help="Show the most recently touched project.")
    last_parser.add_argument(
        "--since",
        default=None,
        help="Show every project touched within this window instead, e.g. '24h' or '7d'.",
    )
    last_parser.set_defaults(func=cmd_last)

    subparsers.add_parser("list", help="List all tracked projects.").set_defaults(func=cmd_list)

    search_parser = subparsers.add_parser(
        "search", help="Search every tracked project's state file for a keyword."
    )
    search_parser.add_argument("keyword", help="The keyword to search for.")
    search_parser.set_defaults(func=cmd_search)

    sync_parser = subparsers.add_parser(
        "sync", help="Merge the local registry with a shared registry file."
    )
    sync_parser.add_argument("shared_path", help="Path to the shared registry JSON file.")
    sync_parser.set_defaults(func=cmd_sync)

    return parser


def _report_broken_pipe() -> None:
    """Silence ``BrokenPipeError`` when output is piped into a command that closes early.

    This is the pattern recommended by the Python documentation: redirect
    stdout to ``os.devnull`` so the interpreter's implicit flush at shutdown
    does not raise a second time.
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``mem`` CLI.

    Args:
        argv: Optional argument list, defaulting to ``sys.argv[1:]``. Supplied
            explicitly by tests.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except MemError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:
        _report_broken_pipe()
        sys.exit(0)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
