from __future__ import annotations

import typer

from ...state import get_state

state = get_state()

# Create a command group
app = typer.Typer(
    name="cache",
    help="Manage the CLI REPL cache.",
    no_args_is_help=True,
    hidden=True,
    deprecated=True,
)
