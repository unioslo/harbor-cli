from __future__ import annotations

from enum import Enum


class OutputFormat(Enum):
    """Output format of the command result."""

    JSON = "json"
    TABLE = "table"
    # others...?
