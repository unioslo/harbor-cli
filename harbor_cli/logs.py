from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .config import LoggingSettings


import logging


# Create logger
logger = logging.getLogger("harbor-cli")
logger.setLevel(logging.DEBUG)  # Capture all log messages


class LogLevel(Enum):
    """Enum for log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
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

    def as_int(self) -> int:
        """Return the stdlib log level int corresponding to the level."""
        res = logging.getLevelName(self.value)
        if not isinstance(res, int):
            return logging.NOTSET
        return res


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


_LOGGING_INIT = False


def setup_logging(config: LoggingSettings) -> None:
    """Set up stderr logging."""
    global _LOGGING_INIT
    if _LOGGING_INIT:  # prevent re-configuring in REPL
        return

    # Create file handler for detailed logs
    file_handler = logging.FileHandler(config.path)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(module)s:%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _LOGGING_INIT = True


def disable_logging() -> None:
    """Disable logging."""
    logger.handlers.clear()
