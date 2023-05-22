from __future__ import annotations

import typer
from trogon import Trogon
from typer.main import get_group

from ...app import app


@app.command()
def tui(
    ctx: typer.Context,  # REPL options
) -> None:
    """Start a TUI (text-based user interface)."""
    Trogon(get_group(app), click_context=ctx, app_name="harbor").run()
