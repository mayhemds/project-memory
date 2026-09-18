"""Filesystem primitives: atomic writes and advisory file locking.

Two problems make naive ``Path.write_text`` unsafe for this tool:

1. **Torn writes.** A crash or power loss midway through a write leaves a
   truncated file. We write to a temporary file in the same directory and
   atomically ``os.replace`` it into position, so readers only ever see the
   old complete file or the new complete file.
2. **Lost updates.** Two ``mem`` processes editing the same registry can
   interleave read-modify-write cycles and silently drop one another's
   changes. An advisory lock around the whole cycle serialises them.

Locking uses :mod:`fcntl`, which is POSIX-only. On platforms without it the
lock degrades to a no-op rather than failing, so the tool still works (with
the original lost-update caveat) outside Unix.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .exceptions import RegistryError, StorageError

try:  # pragma: no cover - import guard, exercised on POSIX where fcntl exists
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None  # type: ignore[assignment]

_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_POLL_SECONDS = 0.05


def _fsync_directory(directory: Path) -> None:
    """Best-effort fsync of a directory so a rename is durable.

    Failures are ignored: some filesystems do not permit opening a directory
    for fsync, and the rename itself has already succeeded by the time this
    runs. Durability across power loss is a bonus, not a correctness
    requirement for this tool.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_text(path: Path, content: str) -> None:
    """Write `content` to `path` atomically, creating parent directories.

    Args:
        path: Destination file path.
        content: Full text content to write.

    Raises:
        StorageError: If the file or its directory cannot be written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise
        _fsync_directory(path.parent)
    except OSError as exc:
        raise StorageError(f"Could not write {path}: {exc}") from exc


def read_text(path: Path) -> str:
    """Read a UTF-8 text file.

    Raises:
        StorageError: If the file cannot be read.
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc}") from exc


@contextmanager
def file_lock(path: Path, *, timeout: float = _LOCK_TIMEOUT_SECONDS) -> Iterator[None]:
    """Hold an exclusive advisory lock on a lock file derived from `path`.

    The lock protects a whole read-modify-write cycle. It is released when the
    context exits, including on exception.

    Args:
        path: The file whose mutation is being protected. A sibling file named
            ``<path>.lock`` is created for the lock itself.
        timeout: Seconds to wait for the lock before giving up.

    Raises:
        StorageError: If the lock cannot be acquired within `timeout`.
    """
    if fcntl is None:  # pragma: no cover - non-POSIX fallback
        yield
        return

    lock_path = path.with_name(f"{path.name}.lock")
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = lock_path.open("w", encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Could not open lock file {lock_path}: {exc}") from exc

    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise StorageError(
                        f"Could not acquire lock on {lock_path} within {timeout:.0f}s. "
                        "Another 'mem' process may be stuck."
                    ) from None
                time.sleep(_LOCK_POLL_SECONDS)
        yield
    finally:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()


def load_json(path: Path, *, source_label: str) -> object:
    """Read and JSON-decode a file, raising :class:`RegistryError` on bad JSON.

    Missing files are the caller's concern; callers check existence first so
    they can distinguish "empty registry" from "corrupt registry".

    Raises:
        RegistryError: If the file exists but is not valid JSON.
        StorageError: If the file exists but cannot be read.
    """
    text = read_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"{source_label} at {path} is corrupted: {exc}") from exc
