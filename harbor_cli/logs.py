from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger as logger


if TYPE_CHECKING:
    from .config import LoggingSettings
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

LOGGER_STDERR_ID: int | None = None
LOGGER_FILE_ID: int | None = None


def setup_logging(config: LoggingSettings) -> None:
    """Set up stderr logging."""
    # Avoid reconfiguring logger if we have already set it up (REPL)
    global LOGGER_STDERR_ID
    global LOGGER_FILE_ID

    if LOGGER_STDERR_ID is not None and LOGGER_FILE_ID is not None:
        return
    elif LOGGER_STDERR_ID is None and LOGGER_FILE_ID is None:
        logger.remove()  # remove default logging handler

    # stderr logger
    if LOGGER_STDERR_ID is None:
        LOGGER_STDERR_ID = logger.add(
            sink=sys.stderr,
            level=config.level.value,
            format=_formatter,
        )

    # File logger
    if LOGGER_FILE_ID is None:
        logfile = config.directory / config.filename
        LOGGER_FILE_ID = logger.add(
            sink=str(logfile),
            level=config.level.value,
        )


def disable_logging() -> None:
    """Disable logging."""
    logger.remove()


def _formatter(record: Record) -> str:
    """Format log messages for Loguru logger."""
    level = record["level"].name
    color = COLORS.get(level, COLOR_DEFAULT)
    message = record["message"]
    message = message.replace("{", "{{").replace("}", "}}")
    return f"<{color}><bold>[{level}]</bold> {message}</{color}>\n"
