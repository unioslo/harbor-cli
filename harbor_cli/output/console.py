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
    style="red",
    highlight=False,
    soft_wrap=True,
)


def success(message: str) -> None:
    """Prints a message to the default console.

    Parameters
    ----------
    msg : str
        Message to print.
    """
    console.print(message, style="green")


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
