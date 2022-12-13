from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer
from harborapi.models.models import Schedule
from harborapi.models.models import ScheduleObj
from harborapi.models.models import Type as ScheduleType

from ...exceptions import HarborCLIError
from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_help
from ...utils import inject_query
from ...utils import inject_sort

# Create a command group
app = typer.Typer(name="gc", help="Garbage collection commands", no_args_is_help=True)

schedule_cmd = typer.Typer(
    name="schedule", help="Garbage collection scheduling", no_args_is_help=True
)
app.add_typer(schedule_cmd)


# HarborAsyncClient.get_gc_schedule()
@schedule_cmd.command("get")
def get_gc_schedule(ctx: typer.Context) -> None:
    """Get garbage collection schedule."""
    logger.info(f"Fetching Garbage Collection schedule...")
    schedule = state.run(state.client.get_gc_schedule())
    render_result(schedule, ctx)


@inject_help(ScheduleObj)
@inject_help(Schedule)
def _do_handle_gc_command(
    ctx: typer.Context,
    type: Optional[ScheduleType] = typer.Option(
        None,
        "--type",
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
    ),
    next_scheduled_time: Optional[datetime] = typer.Option(
        None,
        "--next_scheduled_time",
    ),
) -> None:
    schedule_obj = ScheduleObj(
        type=type,
        cron=cron,
        next_scheduled_time=next_scheduled_time,
    )
    # TODO: investigate which parameters the `parameters` field takes
    schedule = Schedule(schedule=schedule_obj)
    if ctx.command.name == "create":
        logger.info(f"Creating Garbage Collection schedule...")
        state.run(state.client.create_gc_schedule(schedule))
        logger.info(f"Garbage Collection schedule created.")
    elif ctx.command.name == "update":
        logger.info(f"Updating Garbage Collection schedule...")
        state.run(state.client.update_gc_schedule(schedule))
        logger.info(f"Garbage Collection schedule updated.")
    else:
        raise HarborCLIError(f"Unknown command {ctx.command.name}")


# 'gc schedule create' and 'gc schedule update' take the same parameters,
# and only differ in which method is called on the client. To simplify
# the code, we use a single function to handle both commands.

# HarborAsyncClient.create_gc_schedule()
schedule_cmd.command("create", help="Create a new Garbage Collection schedule.")(
    _do_handle_gc_command
)
# HarborAsyncClient.update_gc_schedule()
schedule_cmd.command("update", help="Update existing Garbage Collection schedule.")(
    _do_handle_gc_command
)

# HarborAsyncClient.get_gc_jobs()
@app.command("jobs", no_args_is_help=True)
@inject_query()
@inject_sort()
def get_gc_jobs(ctx: typer.Context, query: Optional[str], sort: Optional[str]) -> None:
    """Get garbage collection jobs."""
    logger.info(f"Fetching Garbage Collection jobs...")
    jobs = state.run(state.client.get_gc_jobs(query=query, sort=sort))
    render_result(jobs, ctx)


# HarborAsyncClient.get_gc_job()
@app.command("job", no_args_is_help=True)
def get_gc_job(
    ctx: typer.Context,
    job_id: int = typer.Argument(
        ..., help="The ID of the Garbage Collection job to fetch."
    ),
) -> None:
    """Get garbage collection job by its ID."""
    logger.info(f"Fetching Garbage Collection jobs...")
    job = state.run(state.client.get_gc_job(job_id))
    render_result(job, ctx)


# HarborAsyncClient.get_gc_log()
@app.command("log", no_args_is_help=True)
def get_gc_log(
    ctx: typer.Context,
    job_id: int = typer.Argument(
        ..., help="The ID of the Garbage Collection job to fetch logs for."
    ),
) -> None:
    """Get garbage collection job by its ID."""
    logger.info(f"Fetching Garbage Collection jobs...")
    log_lines = state.run(state.client.get_gc_log(job_id, as_list=True))
    render_result(log_lines, ctx)
