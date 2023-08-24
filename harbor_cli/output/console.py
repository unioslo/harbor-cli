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


def info(message: str, *args, **kwargs) -> None:
    """Prints an unstyled message to the stderr console."""
    logger.info(message)


def success(message: str, *args, **kwargs) -> None:
    """Prints a green message to the stderr console."""
    logger.info(message)


def warning(message: str, *args, **kwargs) -> None:
    """Prints a yellow message with a warning prefix to the stderr console."""
    logger.warning(message)


def error(message: str, *args, **kwargs) -> None:
    """Prints a red message with an error prefix to the stderr console."""
    logger.error(message)


def exit(message: Optional[str] = None, code: int = 0) -> NoReturn:
    """Prints a message to the default console and exits with the given
    code (default: 0).

    Parameters
    ----------
    message : str
        Message to print.
    code : int, optional
        Exit code, by default 0
    """
    if message:
        logger.info(message)
    raise SystemExit(code)


def exit_err(message: str, code: int = 1, **extra: Any) -> NoReturn:
    """Prints a message to the error console and exits with the given
    code (default: 1).

    Parameters
    ----------
    message : str
        Message to print.
    code : int, optional
        Exit code, by default 1
    """
    logger.error(message, extra=dict(**extra))
    raise SystemExit(code)
