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
    logger.info(message, extra=dict(**kwargs))


def success(message: str, *args, **kwargs) -> None:
    logger.info(message, extra=dict(**kwargs))


def warning(message: str, *args, **kwargs) -> None:
    logger.warning(message, extra=dict(**kwargs))


def error(message: str, *args, **kwargs) -> None:
    logger.error(message, extra=dict(**kwargs))


def exit(message: Optional[str] = None, code: int = 0, **kwargs) -> NoReturn:
    """Logs a message with INFO level and exits with the given code (default: 0)

    Parameters
    ----------
    message : str
        Message to print.
    code : int, optional
        Exit code, by default 0
    **kwargs
        Additional keyword arguments to pass to the extra dict.
    """
    if message:
        info(message, **kwargs)
    raise SystemExit(code)


def exit_err(message: str, code: int = 1, **kwargs: Any) -> NoReturn:
    """Logs a message with ERROR level and exits with the given
    code (default: 1).

    Parameters
    ----------
    message : str
        Message to print.
    code : int, optional
        Exit code, by default 1
    **kwargs
        Additional keyword arguments to pass to the extra dict.
    """
    error(message, **kwargs)
    raise SystemExit(code)
