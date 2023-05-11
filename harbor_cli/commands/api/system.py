from __future__ import annotations

import time

import typer

from ...output.render import render_result
from ...state import get_state

state = get_state()

# Create a command group
app = typer.Typer(
    name="system",
    help="System information",
    no_args_is_help=True,
)


@app.command("info")
def info(ctx: typer.Context) -> None:
    """Get information about the system."""
    system_info = state.run(state.client.get_system_info(), "Fetching system info...")
    render_result(system_info, ctx)


@app.command("volumes")
def volumeinfo(ctx: typer.Context) -> None:
    """Get information about the system volumes."""
    volume_info = state.run(
        state.client.get_system_volume_info(), "Fetching system volume info..."
    )
    render_result(volume_info, ctx)


@app.command("health")
def health(ctx: typer.Context) -> None:
    """Get system health."""
    # NOTE: this is under the /health endpoint, not /system/health
    # but it is still a system health check, hence why it is here,
    # and not in its own health.py file.
    health_status = state.run(state.client.health_check(), "Fetching health info...")
    render_result(health_status, ctx)


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    """Ping the harbor server. Returns the time it took to ping the server in milliseconds."""
    # Use perf_counter with nanosecond resolution to get the most accurate time
    start = time.perf_counter_ns()
    state.run(state.client.ping(), "Pinging server...")
    end = time.perf_counter_ns()
    duration_ms = (end - start) / 1000000
    render_result(duration_ms, ctx)


@app.command("statistics")
def statistics(ctx: typer.Context) -> None:
    """Get statistics about the system."""
    statistics = state.run(state.client.get_statistics(), "Fetching statistics...")
    render_result(statistics, ctx)
