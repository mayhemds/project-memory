"""Cross-project session memory for developers who work across many repos."""

from __future__ import annotations

from .exceptions import MemError
from .statefile import STATE_DIR_NAME, STATE_FILE_NAME

__version__ = "0.1.0"

__all__ = ["STATE_DIR_NAME", "STATE_FILE_NAME", "MemError", "__version__"]
