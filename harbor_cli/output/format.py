from __future__ import annotations

from enum import Enum


class OutputFormat(Enum):
    """Output format of the command result."""

    TABLE = "table"
    JSON = "json"
    # others...?
