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


# TODO: consolidate this metadata with the enum

OUTPUTFORMAT_REPR = {
    OutputFormat.TABLE: "table",
    OutputFormat.JSON: "JSON",
    OutputFormat.JSONSCHEMA: "JSON+Schema",
}

OUTPUTFORMAT_EMOJI = {
    OutputFormat.TABLE: ":page_facing_up:",
    OutputFormat.JSON: ":package:",
    OutputFormat.JSONSCHEMA: ":package:+:memo:",
}


def output_format_repr(fmt: OutputFormat) -> str:
    """Return a human-readable representation of an output format."""
    f = OUTPUTFORMAT_REPR.get(fmt)
    if f is None:
        logger.warning(f"Unknown output format: {fmt}")
        f = "Unknown"
    return f


def output_format_emoji(fmt: OutputFormat) -> str:
    """Return an emoji for an output format."""
    f = OUTPUTFORMAT_EMOJI.get(fmt)
    if f is None:
        logger.warning(f"Unknown output format: {fmt}")
        f = ":question:"
    return f
