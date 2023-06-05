from __future__ import annotations

import typer
from trogon import Trogon
from typer.main import get_group

from ...app import app
from ...output.console import exit_err
from ...state import get_state


@app.command()
def tui(
    ctx: typer.Context,  # REPL options
) -> None:
    """Start a TUI (text-based user interface)."""
    state = get_state()
    if state.repl:
        exit_err(
            f"Cannot launch TUI from REPL mode. Exit REPL and run [italic]harbor tui[/italic]."
        )
    Trogon(get_group(app), click_context=ctx, app_name="harbor").run()
