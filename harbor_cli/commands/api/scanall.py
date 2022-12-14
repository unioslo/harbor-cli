from __future__ import annotations

from typing import Optional

import typer
from harborapi.models import Schedule
from harborapi.models import ScheduleObj

from ...exceptions import HarborCLIError
from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_help

# Create a command group
app = typer.Typer(name="scan-all", help="Manage 'Scan All'.", no_args_is_help=True)
schedule_cmd = typer.Typer(
    name="schedule", help="Manage 'Scan All' schedule.", no_args_is_help=True
)
app.add_typer(schedule_cmd)


# HarborAsyncClient.get_scan_all_metrics()
@app.command("metrics")
def get_scanall_metrics(ctx: typer.Context) -> None:
    """Get metrics for all 'Scan All' jobs."""
    logger.info(f"Fetching metrics for 'Scan All' jobs...")
    metrics = state.run(state.client.get_scan_all_metrics())
    render_result(metrics, ctx)


# HarborAsyncClient.get_scan_all_schedule()
@schedule_cmd.command("get")
def get_scanall_schedule(ctx: typer.Context) -> None:
    """Get the current 'Scan All' schedule."""
    logger.info(f"Fetching 'Scan All' schedule...")
    schedule = state.run(state.client.get_scan_all_schedule())
    render_result(schedule, ctx)


# TODO: deduplicate all code involving Schedule and ScheduleObj
#       (see harbor_cli/commands/api/gc.py)
#       This is basically a copy-paste of the code from gc.py


@inject_help(Schedule)
@inject_help(ScheduleObj)
def _do_handle_schedule_modification_command(
    ctx: typer.Context,
    type: Optional[str] = typer.Option(None, "--type"),
    cron: Optional[str] = typer.Option(None, "--cron"),
) -> None:
    schedule_obj = ScheduleObj(
        type=type,
        cron=cron,
    )
    schedule = Schedule(schedule=schedule_obj)
    if ctx.command.name == "create":
        logger.info(f"Creating 'Scan All' schedule...")
        state.run(state.client.create_scan_all_schedule(schedule))
        logger.info(f"'Scan All' schedule created.")
    elif ctx.command.name == "update":
        logger.info(f"Updating 'Scan All' schedule...")
        state.run(state.client.create_scan_all_schedule(schedule))
        logger.info(f"'Scan All' schedule updated.")
    else:
        raise HarborCLIError(f"Unknown command {ctx.command.name}")


# 'scan-all schedule create' and 'scan-all schedule update' take the same parameters,
# and only differ in which method is called on the client. To simplify
# the code, we use a single function to handle both commands.


# HarborAsyncClient.create_scan_all_schedule()
schedule_cmd.command("create", help="Create a new Garbage Collection schedule.")(
    _do_handle_schedule_modification_command
)
# HarborAsyncClient.update_scan_all_schedule()
schedule_cmd.command("update", help="Update existing Garbage Collection schedule.")(
    _do_handle_schedule_modification_command
)

# HarborAsyncClient.stop_scan_all_job()
@app.command("stop")
def stop_scanall_job(ctx: typer.Context) -> None:
    """Stop the currently running 'Scan All' job."""
    logger.info(f"Stopping 'Scan All' job...")
    state.run(state.client.stop_scan_all_job())
    logger.info(f"'Scan All' job stopped.")
