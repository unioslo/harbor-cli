"""Output format of the command result."""
from __future__ import annotations

from enum import Enum

from ..logs import logger


class OutputFormat(Enum):
    """Output format of the command result."""

    TABLE = "table"
    JSON = "json"
    JSONSCHEMA = "jsonschema"
    # others...?


OUTPUTFORMAT_REPR = {
    OutputFormat.TABLE: "table",
    OutputFormat.JSON: "JSON",
    OutputFormat.JSONSCHEMA: "JSON+Schema",
}


def output_format_repr(fmt: OutputFormat) -> str:
    """Return a human-readable representation of an output format."""
    f = OUTPUTFORMAT_REPR.get(fmt)
    if f is None:
        logger.warning(f"Unknown output format: {fmt}")
        f = "Unknown"
    return f
