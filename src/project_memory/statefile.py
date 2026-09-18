"""Reading and writing a project's human-readable ``.memory/STATE.md`` file.

The state file is intentionally plain markdown so any editor, IDE, or AI
assistant can read and write it. This module owns the two operations that
mutate it: creating the initial file and appending a session entry, both of
which write atomically and preserve the file's frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import ProjectNotInitializedError, StateFileError
from .storage import atomic_write_text, file_lock, read_text

STATE_DIR_NAME = ".memory"
STATE_FILE_NAME = "STATE.md"

STATE_TEMPLATE = """---
project: {name}
status: in-progress
last_updated: {timestamp}
---

# {name}

## Current focus
(what you're actively doing right now, one line)

## Open issues / bugs
-

## Next steps / todo
-

## Recent decisions
-

## Session log
"""


def state_file(project_root: Path) -> Path:
    """Return the path to a project's state file."""
    return project_root / STATE_DIR_NAME / STATE_FILE_NAME


def find_project_root(start: Path) -> Path:
    """Walk upward from `start` looking for a directory containing ``.memory/``.

    Falls back to `start` itself when no initialized project is found, so the
    calling command can raise a precise "run 'mem init'" error rather than
    silently operating on an unrelated directory.

    Args:
        start: Directory to begin the search from (typically the cwd).

    Returns:
        The nearest ancestor that contains a ``.memory`` directory, or
        `start` resolved if there is none.
    """
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / STATE_DIR_NAME).is_dir():
            return candidate
    return current


def initialize_project(project_root: Path, timestamp: str) -> Path:
    """Create the initial state file for a project.

    Args:
        project_root: Directory to initialize.
        timestamp: ISO timestamp recorded in the frontmatter.

    Returns:
        The path of the newly created state file.

    Raises:
        StateFileError: If a state file already exists at this location.
        StorageError: If the file cannot be written.
    """
    path = state_file(project_root)
    if path.exists():
        raise StateFileError(f"{path} already exists. This project is already tracked.")
    content = STATE_TEMPLATE.format(name=project_root.name, timestamp=timestamp)
    atomic_write_text(path, content)
    return path


def read_state(project_root: Path) -> str:
    """Return the raw text of a project's state file.

    Raises:
        ProjectNotInitializedError: If the project has no state file.
        StorageError: If the file exists but cannot be read.
    """
    path = state_file(project_root)
    if not path.exists():
        raise ProjectNotInitializedError(f"No memory file found at {path}. Run 'mem init' first.")
    return read_text(path)


def _update_frontmatter_field(content: str, field_name: str, value: str) -> str:
    """Replace a single ``key: value`` line inside a frontmatter block.

    The file's trailing newline (or lack of one) is preserved exactly.

    Raises:
        StateFileError: If the file has no frontmatter block or lacks the field.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise StateFileError("State file is missing its frontmatter block.")
    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise StateFileError("State file's frontmatter block is not closed.")
    for index in range(1, closing_index):
        if lines[index].startswith(f"{field_name}:"):
            lines[index] = f"{field_name}: {value}"
            break
    else:
        raise StateFileError(f"Frontmatter field {field_name!r} not found in state file.")
    trailing_newline = "\n" if content.endswith("\n") else ""
    return "\n".join(lines) + trailing_newline


def append_session_entry(project_root: Path, note: str, timestamp: str) -> Path:
    """Append a session entry and refresh the frontmatter timestamp in one write.

    Both mutations are applied in memory and flushed with a single atomic
    write under an advisory lock. This closes the window in the original
    implementation where a crash between the append and the frontmatter update
    could leave an entry with a stale timestamp, and where two concurrent
    saves could drop one another's entry.

    Args:
        project_root: Root of the initialized project.
        note: The session note text.
        timestamp: ISO timestamp for both the entry heading and frontmatter.

    Returns:
        The path of the state file that was written.

    Raises:
        ProjectNotInitializedError: If the project has no state file.
        StateFileError: If the existing file has malformed frontmatter.
    """
    path = state_file(project_root)
    if not path.exists():
        raise ProjectNotInitializedError(f"No memory file found at {path}. Run 'mem init' first.")
    with file_lock(path):
        content = read_text(path)
        updated = _update_frontmatter_field(content, "last_updated", timestamp)
        if not updated.endswith("\n"):
            updated += "\n"
        updated += f"\n### {timestamp}\n- {note}\n"
        atomic_write_text(path, updated)
    return path
