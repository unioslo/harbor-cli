from __future__ import annotations

import typer
from click_repl import repl as start_repl

from ...app import app
from ...state import state


@app.command()
def repl(ctx: typer.Context) -> None:
    """Start an interactive REPL."""
    state.repl = True
    start_repl(ctx)
