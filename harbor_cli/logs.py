from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .config import LoggingSettings


import logging


# Create logger
logger = logging.getLogger("harbor-cli")
logger.setLevel(logging.DEBUG)  # Capture all log messages
logger.disabled = True
logger.handlers.clear()


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

    @classmethod
    def levels(cls) -> dict[LogLevel, int]:
        """Return a dict of all log levels and their corresponding int values."""
        return {level: level.as_int() for level in cls}


def setup_logging(config: LoggingSettings) -> None:
    """Set up file logging."""
    if not logger.disabled:  # prevent re-configuring in REPL
        return
    file_handler = _get_file_handler(config)
    logger.addHandler(file_handler)
    logger.disabled = False


def _get_file_handler(config: LoggingSettings) -> logging.FileHandler:
    file_handler = logging.FileHandler(config.path)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(module)s:%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(config.level.as_int())
    return file_handler


def update_logging(config: LoggingSettings) -> None:
    """Update logging configuration."""
    if logger.handlers:
        if not config.enabled:
            disable_logging()
        else:
            file_handler = _get_file_handler(config)
            replace_handler(file_handler)
    else:
        setup_logging(config)


def replace_handler(handler: logging.Handler) -> None:
    """Replace the file handler with the given handler."""
    logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)


def disable_logging() -> None:
    """Disable logging."""
    logger.handlers.clear()
    logger.disabled = True
