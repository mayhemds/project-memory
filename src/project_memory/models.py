"""Validated data models for the project registry.

The registry is a JSON file a user can hand-edit, a teammate can sync, or a
crash can truncate. Every field is therefore validated on load rather than
trusted. Validation failures are translated into :class:`RegistryError` so the
CLI reports a clean message instead of a raw pydantic traceback.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .exceptions import RegistryError

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M"
_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


class Project(BaseModel):
    """A single tracked project in the global registry.

    Unknown keys are ignored rather than rejected, so a registry written by a
    newer version of this tool still loads under an older one.
    """

    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=256)
    path: str = Field(min_length=1, max_length=4096)
    last_updated: str

    @field_validator("last_updated")
    @classmethod
    def _validate_timestamp(cls, value: str) -> str:
        """Reject timestamps that are not zero-padded ``YYYY-MM-DDTHH:MM``."""
        if not _TIMESTAMP_PATTERN.match(value):
            raise ValueError(f"must look like YYYY-MM-DDTHH:MM, got {value!r}")
        try:
            datetime.strptime(value, TIMESTAMP_FORMAT)
        except ValueError as exc:
            raise ValueError(f"is not a valid timestamp: {value!r}") from exc
        return value

    @property
    def resolved_path(self) -> Path:
        """Return the stored path as a :class:`Path`."""
        return Path(self.path)


def parse_projects(raw: object, *, source: Path) -> list[Project]:
    """Validate a parsed JSON value into a list of :class:`Project` entries.

    Args:
        raw: The decoded JSON value, expected to be a list of objects each
            containing ``name``, ``path``, and ``last_updated``.
        source: The file `raw` came from, used only in error messages.

    Returns:
        The validated list of projects.

    Raises:
        RegistryError: If `raw` is not a list, or any entry is malformed.
    """
    if not isinstance(raw, list):
        raise RegistryError(
            f"Registry file at {source} should contain a JSON list, found {type(raw).__name__}."
        )
    try:
        return [Project.model_validate(entry) for entry in raw]
    except ValidationError as exc:
        raise RegistryError(
            f"Registry file at {source} has a malformed entry: {exc}. "
            "Each entry needs 'name', 'path', and 'last_updated'."
        ) from exc
