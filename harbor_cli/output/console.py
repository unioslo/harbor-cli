from __future__ import annotations

from typing import Any
from typing import NoReturn
from typing import Optional

from rich.console import Console

from ..logs import logger

_exit = exit  # save the original exit function

console = Console()
err_console = Console(
    stderr=True,
    highlight=False,
    soft_wrap=True,
)


def _add_fix(message: str, prefix: str | None, suffix: str | None = None) -> str:
    if prefix:
        prefix = prefix.strip()
        message = f"{prefix} {message}"
    if suffix:
        suffix = suffix.strip()
        message = f"{message} {suffix}"
    return message


def info(message: str, prefix: str | None = None, suffix: str | None = None) -> None:
    """Prints an unstyled message to the stderr console."""
    message = _add_fix(message, prefix, suffix)
    err_console.print(message)


def success(
    message: str, prefix: str | None = None, suffix: str | None = ":white_check_mark:"
) -> None:
    """Prints a green message to the stderr console."""
    message = _add_fix(message, prefix, suffix)
    err_console.print(message, style="green")


def warning(message: str, prefix: str = "WARNING: ", suffix: str | None = None) -> None:
    """Prints a yellow message with a warning prefix to the stderr console."""
    message = _add_fix(message, prefix, suffix)
    err_console.print(message, style="yellow")


def error(message: str, prefix: str = "ERROR: ", suffix: str | None = None) -> None:
    """Prints a red message with an error prefix to the stderr console."""
    message = _add_fix(message, prefix, suffix)
    err_console.print(message, style="red")


def exit(message: Optional[str] = None, code: int = 0) -> NoReturn:
    """Prints a message to the default console and exits with the given
    code (default: 0).

    Parameters
    ----------
    msg : str
        Message to print.
    code : int, optional
        Exit code, by default 0
    """
    if message:
        logger.info(message)
    raise SystemExit(code)


def exit_err(
    message: str, code: int = 1, prefix: str = "ERROR", **extra: Any
) -> NoReturn:
    """Prints a message to the error console and exits with the given
    code (default: 1).

    Parameters
    ----------
    msg : str
        Message to print.
    code : int, optional
        Exit code, by default 1
    """
    logger.bind(**extra).error(message)
    raise SystemExit(code)
