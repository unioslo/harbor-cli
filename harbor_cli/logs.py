from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger as logger  # re-export

if TYPE_CHECKING:
    from loguru import Record


class LogLevel(Enum):
    """Enum for log levels."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @classmethod
    def _missing_(cls, value: object) -> LogLevel:
        """Convert string to enum value.

        Raises
        ------
        ValueError
            If the value is not a valid log level.
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value)}")
        for member in cls:
            if member.value == value.upper():
                return member
        raise ValueError(f"{value} is not a valid log level.")

    def __str__(self) -> str:
        """Return the enum value as a string."""
        return self.value


COLOR_DEFAULT = "white"
COLORS = {
    "TRACE": "white",
    "DEBUG": "white",
    "INFO": "white",
    "SUCCESS": "white",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red",
}

CONFIGURED_LOGLEVEL = None  # type: str | None


def setup_logging(level: str | LogLevel = "INFO") -> None:
    # Avoid reconfiguring the logger if the level hasn't changed
    global CONFIGURED_LOGLEVEL
    if level == CONFIGURED_LOGLEVEL:
        return
    if isinstance(level, LogLevel):
        level = level.value
    logger.remove()
    logger.add(
        sink=sys.stderr,
        level=level,
        format=_formatter,
    )
    CONFIGURED_LOGLEVEL = level


def disable_logging() -> None:
    """Disable logging."""
    logger.remove()


def _formatter(record: Record) -> str:
    """Format log messages for Loguru logger."""
    level = record["level"].name
    color = COLORS.get(level, COLOR_DEFAULT)
    return f"<{color}><bold>[{level}]</bold> {record['message']}</{color}>\n"
