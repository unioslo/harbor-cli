from __future__ import annotations

from typing import Any
from typing import NoReturn
from typing import Optional

from rich.console import Console

from ..logs import logger
from ..state import get_state
from ..style import Icon
from ..style.color import bold
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


def _do_rule(rule: bool) -> None:
    if rule:
        err_console.rule()


def info(message: str, icon: str = Icon.INFO, rule: bool = False, **kwargs) -> None:
    """Log with INFO level and print an informational message."""
    logger.info(message, extra=dict(**kwargs))
    _do_rule(rule)
    err_console.print(f"{green(icon)} {message}")


def success(message: str, icon: str = Icon.OK, rule: bool = False, **kwargs) -> None:
    """Log with DEBUG level and print a success message."""
    logger.debug(message, extra=dict(**kwargs))
    _do_rule(rule)
    err_console.print(f"{green(icon)} {message}")


def warning(
    message: str, icon: str = Icon.WARNING, rule: bool = False, **kwargs
) -> None:
    """Log with WARNING level and optionally print a warning message."""
    logger.warning(message, extra=dict(**kwargs))
    if get_state().config.general.warnings:
        _do_rule(rule)
        err_console.print(bold(f"{yellow(icon)} {message}"))


def error(
    message: str,
    icon: str = Icon.ERROR,
    exc_info: bool = False,
    rule: bool = False,
    **kwargs,
) -> None:
    """Log with ERROR level and print an error message."""
    logger.error(message, extra=dict(**kwargs), exc_info=exc_info)
    _do_rule(rule)
    err_console.print(bold(f"{red(icon)} {message}"))


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


def print_toml(toml_str: str, end: str = "\n") -> None:
    """Prints TOML to stdout using the default console."""
    console.print(
        toml_str,
        markup=False,  # TOML tables could be interpreted as rich markup
        soft_wrap=True,  # prevents mangling whitespace
        end=end,  # Allow control of trailing newline
    )
