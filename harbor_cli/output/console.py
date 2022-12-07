from __future__ import annotations

from typing import NoReturn

import typer
from rich.console import Console

console = Console()
err_console = Console(stderr=True, style="red")


def exit(msg: str, code: int = 0) -> NoReturn:
    """Prints a message to the default console and exits with the given
    code (default: 0).

    Parameters
    ----------
    msg : str
        Message to print.
    code : int, optional
        Exit code, by default 0
    """
    console.print(msg)
    raise typer.Exit(code)


def exit_err(msg: str, code: int = 1, prefix: str = "ERROR") -> NoReturn:
    """Prints a message to the error console and exits with the given
    code (default: 1).

    Parameters
    ----------
    msg : str
        Message to print.
    code : int, optional
        Exit code, by default 1
    """
    if prefix:
        prefix = f"[bold]{prefix}[/bold]: "
    err_console.print(f"{prefix}{msg}")
    raise typer.Exit(code)
