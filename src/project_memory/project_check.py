"""Sanity checks that run before ``mem init`` creates a state file.

``mem init`` treats the current folder as one project. Running it in the wrong
place, such as a folder that merely holds many projects, is an easy mistake and
a confusing one to undo, so these checks produce human-readable warnings the CLI
can show before anything is written.
"""

from __future__ import annotations

from pathlib import Path

from .statefile import STATE_DIR_NAME

PROJECT_MARKER_NAMES = (
    ".git",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "package.json",
    "deno.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "mix.exs",
    "Package.swift",
    "CMakeLists.txt",
    "Makefile",
)
PROJECT_MARKER_PATTERNS = ("*.sln", "*.csproj")

_MAX_CHILDREN_SCANNED = 200
_MAX_EXAMPLES = 3


def has_project_marker(directory: Path) -> bool:
    """Return True when `directory` holds a file that marks it as a project."""
    try:
        if any((directory / name).exists() for name in PROJECT_MARKER_NAMES):
            return True
        return any(next(directory.glob(pattern), None) for pattern in PROJECT_MARKER_PATTERNS)
    except OSError:
        return False


def _child_projects(directory: Path) -> list[str]:
    """Return names of immediate subfolders that look like projects."""
    found: list[str] = []
    try:
        children = sorted(
            child
            for child in directory.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )[:_MAX_CHILDREN_SCANNED]
    except OSError:
        return found
    for child in children:
        if has_project_marker(child):
            found.append(child.name)
    return found


def init_warnings(root: Path) -> list[str]:
    """Return reasons `root` may be the wrong place to run ``mem init``.

    Args:
        root: The folder ``mem init`` is about to turn into a tracked project.

    Returns:
        Zero or more warning messages. An empty list means nothing looks off.
    """
    root = root.resolve()
    warnings: list[str] = []

    if root == Path(root.anchor) or root == Path.home().resolve():
        warnings.append(
            f"{root} is your home or filesystem root folder, not a project. "
            "Run 'mem init' inside one project folder instead."
        )
    elif not has_project_marker(root):
        children = _child_projects(root)
        if children:
            examples = ", ".join(children[:_MAX_EXAMPLES])
            more = (
                f" and {len(children) - _MAX_EXAMPLES} more"
                if len(children) > _MAX_EXAMPLES
                else ""
            )
            warnings.append(
                f"'{root.name}' has no project files of its own, but it contains "
                f"{len(children)} folder(s) that look like projects ({examples}{more}). "
                "Run 'mem init' inside one of those instead, so each project gets its own notes."
            )
        else:
            names = ", ".join(PROJECT_MARKER_NAMES[:5])
            warnings.append(
                f"No project files found in '{root.name}' (such as {names}). "
                "This does not look like a project folder."
            )

    for parent in root.parents:
        if (parent / STATE_DIR_NAME).is_dir():
            warnings.append(
                f"A parent folder ({parent}) is already tracked. "
                "This would create a separate project nested inside it."
            )
            break

    return warnings
