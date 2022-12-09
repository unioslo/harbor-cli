from __future__ import annotations

import typer

from ...logs import logger
from ...output.console import console
from ...state import state

# Create a command group
app = typer.Typer(name="system")


@app.command("info")
def info(ctx: typer.Context) -> None:
    """Get information about the system."""
    logger.info(f"Fetching system info...")
    system_info = state.loop.run_until_complete(state.client.get_system_info())
    console.print(system_info)


@app.command("volumeinfo")
def volumeinfo(ctx: typer.Context) -> None:
    """Get information about the system volumes."""
    logger.info(f"Fetching system volume info...")
    volume_info = state.run(state.client.get_system_volume_info())
    console.print(volume_info)
