from __future__ import annotations

from typing import Optional

import typer
from harborapi.models import Schedule
from harborapi.models import ScheduleObj

from ...output.console import exit_err
from ...output.console import info
from ...output.render import render_result
from ...state import get_state
from ...utils.args import create_updated_model
from ...utils.args import model_params_from_ctx
from ...utils.commands import inject_help

state = get_state()

# Create a command group
app = typer.Typer(
    name="scan-all",
    help="Scanning of all artifacts.",
    no_args_is_help=True,
)
schedule_cmd = typer.Typer(
    name="schedule",
    help="Manage 'Scan All' schedule.",
    no_args_is_help=True,
)
app.add_typer(schedule_cmd)


# HarborAsyncClient.get_scan_all_metrics()
@app.command("metrics")
def get_scanall_metrics(ctx: typer.Context) -> None:
    """Get metrics for all 'Scan All' jobs."""
    metrics = state.run(
        state.client.get_scan_all_metrics(), "Fetching metrics for 'Scan All' jobs..."
    )
    render_result(metrics, ctx)


def get_scanall_schedule() -> Schedule:
    return state.run(
        state.client.get_scan_all_schedule(), "Fetching 'Scan All' schedule..."
    )


# HarborAsyncClient.get_scan_all_schedule()
@schedule_cmd.command("get")
def get_scanall_schedule_cmd(ctx: typer.Context) -> None:
    """Get the current 'Scan All' schedule."""
    schedule = get_scanall_schedule()
    render_result(schedule, ctx)


@schedule_cmd.command("create")
@inject_help(Schedule)
@inject_help(ScheduleObj)
def create_scanall_schedule(
    ctx: typer.Context,
    type: Optional[str] = typer.Option(None),
    cron: Optional[str] = typer.Option(None),
) -> None:
    params = model_params_from_ctx(ctx, ScheduleObj)
    schedule = Schedule(schedule=ScheduleObj(**params))
    state.run(
        state.client.create_scan_all_schedule(schedule),
        "Creating 'Scan All' schedule...",
    )
    info(f"'Scan All' schedule created.")


@schedule_cmd.command("update")
@inject_help(Schedule)
@inject_help(ScheduleObj)
def update_scanall_schedule(
    ctx: typer.Context,
    type: Optional[str] = typer.Option(None),
    cron: Optional[str] = typer.Option(None),
    # TODO: 'parameters' field for Schedule
) -> None:
    schedule = get_scanall_schedule()
    if not schedule.schedule:
        exit_err("No existing 'Scan All' schedule found.")
    schedule_obj = create_updated_model(schedule.schedule, ScheduleObj, ctx)
    schedule.schedule = schedule_obj
    state.run(
        state.client.update_scan_all_schedule(schedule),
        "Updating 'Scan All' schedule...",
    )
    info(f"'Scan All' schedule created.")


# HarborAsyncClient.stop_scan_all_job()
@app.command("stop")
def stop_scanall_job(ctx: typer.Context) -> None:
    """Stop the currently running 'Scan All' job."""
    state.run(state.client.stop_scan_all_job(), "Stopping 'Scan All' job...")
    info(f"'Scan All' job stopped.")
