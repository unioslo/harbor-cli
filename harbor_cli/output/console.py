from __future__ import annotations

from typing import Any
from typing import NoReturn
from typing import Optional
from typing import TYPE_CHECKING

from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule

from ..logs import logger
from ..state import get_state
from ..style import Icon
from ..style.color import bold as bold_func
from ..style.color import Color
from ..style.color import get_color_func

if TYPE_CHECKING:
    from rich.console import RenderableType  # noqa: F401

# stdout console used to print results
console = Console()

# stderr console used to print prompts, messages, etc.
err_console = Console(
    stderr=True,
    highlight=False,
    soft_wrap=True,
)


def get_renderable(
    message: str,
    icon: Icon | str,  # stupid mypy hack since it doesn't understand StrEnum here
    color: Color,
    preamble: str | None = None,
    color_all: bool = False,
    bold: bool = False,
    panel: bool = False,
    rule: bool = False,
) -> Group:
    """Constructs a renderable object for printing to the console.

    Parameters
    ----------
    message : str
        Message to print.
    icon : Icon
        Icon to use.
    color : Color
        Color to use for the icon.
    preamble : str, optional
        Preamble to print before the message, by default None
        Trailing colon and whitespace are removed.
    color_all : bool, optional
        Whether to color the entire message, by default False
        Only colors the icon if False.
    bold : bool, optional
        Whether to bold the message, by default False
    panel : bool, optional
        Whether to wrap the message in a panel, by default False
    rule : bool, optional
        Whether to print a rule (line) before the message, by default False

    Returns
    -------
    Group
        A group of renderables to print.
    """
    # NOTE: A rich.Group is immutable, so we have to collect renderables first
    renderables = []  # type: list[RenderableType]
    if rule:
        renderables.append(Rule(style="rule.line"))

    color_func = get_color_func(color)
    msg = message

    # Add preamble in bold, separated with colon
    if preamble:
        preamble = preamble.strip(": ")  # remove colon and whitespace
        msg = f"{bold_func(color_func(preamble))}: {message}"

    # Format the icon and message
    msg = f"{bold_func(color_func(icon))} {msg}"
    if color_all:
        msg = color_func(msg)  # HACK: we just call the color func again here
    if bold:
        msg = bold_func(msg)

    if panel:
        renderables.append(Panel(msg, expand=False))
    else:
        renderables.append(msg)

    return Group(*renderables)


def info(
    message: str,
    panel: bool = False,
    rule: bool = False,
    **kwargs,
) -> None:
    """Log with INFO level and print an informational message."""
    logger.info(message, extra=dict(**kwargs))
    err_console.print(
        get_renderable(message, Icon.INFO, "green", panel=panel, rule=rule)
    )


def success(
    message: str,
    panel: bool = False,
    rule: bool = False,
    **kwargs,
) -> None:
    """Log with DEBUG level and print a success message."""
    logger.debug(message, extra=dict(**kwargs))
    err_console.print(
        get_renderable(message, Icon.OK, "green", panel=panel, rule=rule),
    )


def warning(
    message: str,
    rule: bool = False,
    panel: bool = False,
    **kwargs,
) -> None:
    """Log with WARNING level and optionally print a warning message."""
    logger.warning(message, extra=dict(**kwargs))
    if get_state().config.general.warnings:
        err_console.print(
            get_renderable(
                message,
                icon=Icon.WARNING,
                color="yellow",
                preamble="WARNING",
                color_all=True,  # entire message is yellow
                rule=rule,
                panel=panel,
                bold=True,
            )
        )


def error(
    message: str,
    rule: bool = False,
    panel: bool = False,
    exc_info: bool = False,
    **kwargs,
) -> None:
    """Log with ERROR level and print an error message."""
    logger.error(message, extra=dict(**kwargs), exc_info=exc_info)
    err_console.print(
        get_renderable(
            message, icon=Icon.ERROR, color="red", rule=rule, panel=panel, bold=True
        )
    )


def exit_ok(message: Optional[str] = None, code: int = 0, **kwargs) -> NoReturn:
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
