"""Exception hierarchy for project-memory.

Every expected, user-facing failure raised by this package derives from
:class:`MemError`, so the CLI layer can catch a single base type and print a
clean message instead of leaking a traceback to the terminal.
"""

from __future__ import annotations


class MemError(Exception):
    """Base class for all expected, user-facing failures."""


class RegistryError(MemError):
    """The global project registry is missing, corrupt, or malformed."""


class StateFileError(MemError):
    """A project's ``.memory/STATE.md`` file is missing or malformed."""


class ProjectNotInitializedError(MemError):
    """A command required an initialized project but found none."""


class StorageError(MemError):
    """A filesystem read or write could not be completed."""


class AIError(MemError):
    """An AI drafting operation failed (missing configuration or API failure)."""
