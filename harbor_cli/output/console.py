from __future__ import annotations

from typing import Any
from typing import NoReturn
from typing import Optional

from rich.console import Console

from ..style import Icon
from ..style.color import green
from ..style.color import red
from ..style.color import yellow

_exit = exit  # save the original exit function

# stdout console used to print results
console = Console()

# stderr console used to print prompts, messages, etc.
err_console = Console(
    stderr=True,
    highlight=False,
    soft_wrap=True,
)


def info(message: str, icon: str = Icon.INFO, *args, **kwargs) -> None:
    # logger.info(message, extra=dict(**kwargs))
    err_console.print(f"{green(icon)} {message}")


def success(message: str, icon: str = Icon.OK, **kwargs) -> None:
    # logger.info(message, extra=dict(**kwargs))
    err_console.print(f"{green(icon)} {message}")


def warning(message: str, icon: str = Icon.WARNING, **kwargs) -> None:
    # logger.warning(message, extra=dict(**kwargs))
    err_console.print(f"{yellow(icon)} {message}")


def error(message: str, icon: str = Icon.ERROR, **kwargs) -> None:
    # logger.error(message, extra=dict(**kwargs))
    err_console.print(f"{red(icon)} {message}")


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
