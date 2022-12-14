from __future__ import annotations

import time

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


@app.command("volumes")
def volumeinfo(ctx: typer.Context) -> None:
    """Get information about the system volumes."""
    logger.info(f"Fetching system volume info...")
    volume_info = state.run(state.client.get_system_volume_info())
    render_result(volume_info, ctx)


@app.command("health")
def get_health(ctx: typer.Context) -> None:
    """Get system health.

    NOTE: this is under the /health endpoint, not /system/health
    but it is still a system health check, hence why it is here,
    and not in its own health.py file.
    """
    logger.info(f"Fetching health info...")
    health_status = state.run(state.client.health_check())
    render_result(health_status, ctx)


@app.command("ping")
def ping_harbor(ctx: typer.Context) -> None:
    """Ping the harbor server. Returns the time it took to ping the server in milliseconds."""
    logger.info(f"Pinging server...")
    # Use perf_counter with nanosecond resolution to get the most accurate time
    start = time.perf_counter_ns()
    state.run(state.client.ping())
    end = time.perf_counter_ns()
    duration_ms = (end - start) / 1000000
    render_result(duration_ms, ctx)
