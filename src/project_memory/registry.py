"""The global project registry: loading, saving, upsert, and team sync.

The registry is a JSON list of :class:`~project_memory.models.Project` entries
stored under :func:`~project_memory.config.registry_file`. Mutations hold an
advisory lock for the whole read-modify-write cycle and land on disk via an
atomic write, so concurrent invocations cannot lose each other's updates.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import registry_dir, registry_file
from .exceptions import RegistryError
from .models import Project, parse_projects
from .storage import atomic_write_text, file_lock, load_json


def load_registry() -> list[Project]:
    """Load the global registry, returning an empty list when none exists.

    Raises:
        RegistryError: If the registry exists but is not valid JSON or does
            not match the expected shape.
    """
    path = registry_file()
    if not path.exists():
        return []
    raw = load_json(path, source_label="Registry file")
    return parse_projects(raw, source=path)


def _serialize(projects: list[Project]) -> str:
    """Render projects as the pretty-printed JSON stored on disk."""
    return json.dumps([project.model_dump() for project in projects], indent=2)


def save_registry(projects: list[Project], *, path: Path | None = None) -> None:
    """Atomically write the registry (or a shared registry) to disk.

    Args:
        projects: Entries to persist.
        path: Destination file. Defaults to the global registry location.
    """
    destination = path if path is not None else registry_file()
    atomic_write_text(destination, _serialize(projects))


def upsert_project(name: str, path: Path, timestamp: str) -> None:
    """Insert a project into the global registry, or update it if present.

    The whole load-modify-save cycle is performed under the registry lock so
    two concurrent ``mem`` processes cannot both read the same list and then
    clobber each other's additions.

    Args:
        name: Human-readable project name.
        path: Project root; stored resolved so the same directory always maps
            to a single entry.
        timestamp: ISO timestamp of the touch that prompted this update.
    """
    destination = registry_file()
    destination.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(path.resolve())
    with file_lock(destination):
        projects = load_registry()
        for project in projects:
            if project.path == resolved:
                project.name = name
                project.last_updated = timestamp
                break
        else:
            projects.append(Project(name=name, path=resolved, last_updated=timestamp))
        save_registry(projects, path=destination)


def _wins_over(candidate: Project, current: Project) -> bool:
    """Return True when `candidate` should replace `current` during a merge.

    Recency decides, and equal timestamps are broken by name so the result is
    deterministic regardless of which side each entry came from. Without that
    tie-break, two machines merging the same pair of registries with the
    entries on opposite sides would converge to different results and thrash
    on every sync.
    """
    if candidate.last_updated != current.last_updated:
        return candidate.last_updated > current.last_updated
    return candidate.name < current.name


def merge_projects(shared: list[Project], local: list[Project]) -> list[Project]:
    """Merge two registries, keeping the winning entry per project path.

    The more recent timestamp wins; equal timestamps are broken by name so the
    merge is deterministic and order-independent.

    Args:
        shared: Projects read from the shared registry file.
        local: Projects read from the local registry.

    Returns:
        A new list with one entry per unique project path.
    """
    merged: dict[str, Project] = {}
    for project in [*shared, *local]:
        existing = merged.get(project.path)
        if existing is None or _wins_over(project, existing):
            merged[project.path] = project
    return list(merged.values())


def load_shared_registry(shared_path: Path) -> list[Project]:
    """Load a shared registry file, returning an empty list when it is absent.

    Raises:
        RegistryError: If the file exists but is corrupt or malformed.
    """
    if not shared_path.exists():
        return []
    raw = load_json(shared_path, source_label="Shared registry")
    return parse_projects(raw, source=shared_path)


def sync_with_shared(shared_path: Path) -> int:
    """Merge the local registry with a shared file and write both back.

    Both copies end up identical, so running sync repeatedly from any machine
    converges everyone toward the same picture.

    Args:
        shared_path: Path to the shared registry JSON file.

    Returns:
        The number of distinct projects after merging.

    Raises:
        RegistryError: If either registry is corrupt or malformed.
    """
    destination = registry_file()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shared_path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(destination):
        local_projects = load_registry()
        shared_projects = load_shared_registry(shared_path)
        merged = merge_projects(shared_projects, local_projects)
        save_registry(merged, path=destination)
        save_registry(merged, path=shared_path)
    return len(merged)


__all__ = [
    "RegistryError",
    "load_registry",
    "load_shared_registry",
    "merge_projects",
    "registry_dir",
    "save_registry",
    "sync_with_shared",
    "upsert_project",
]
