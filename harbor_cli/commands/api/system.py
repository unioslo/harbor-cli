from __future__ import annotations

import typer

from ...logs import logger
from ...output.render import render_result
from ...state import state

# Create a command group
app = typer.Typer(
    name="system",
    help="System information",
    no_args_is_help=True,
)


@app.command("info")
def info(ctx: typer.Context) -> None:
    """Get information about the system."""
    logger.info(f"Fetching system info...")
    system_info = state.run(state.client.get_system_info())
    render_result(system_info, ctx)


@app.command("volumeinfo")
def volumeinfo(ctx: typer.Context) -> None:
    """Get information about the system volumes."""
    logger.info(f"Fetching system volume info...")
    volume_info = state.run(state.client.get_system_volume_info())
    render_result(volume_info, ctx)
