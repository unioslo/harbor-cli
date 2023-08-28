from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import Schedule
from harborapi.models.models import ScheduleObj
from harborapi.models.models import Type as ScheduleType

from ...output.console import exit_err
from ...output.console import info
from ...output.prompts import check_enumeration_options
from ...output.render import render_result
from ...state import get_state
from ...utils.args import create_updated_model
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options

state = get_state()

# Create a command group
app = typer.Typer(
    name="gc",
    help="Garbage Collection scheduling and information",
    no_args_is_help=True,
)

schedule_cmd = typer.Typer(
    name="schedule", help="Garbage collection scheduling", no_args_is_help=True
)
app.add_typer(schedule_cmd)


# HarborAsyncClient.get_gc_schedule()
@schedule_cmd.command("get")
def get_gc_schedule(ctx: typer.Context) -> None:
    """Get garbage collection schedule."""
    schedule = state.run(
        state.client.get_gc_schedule(), f"Fetching Garbage Collection schedule..."
    )
    render_result(schedule, ctx)


@schedule_cmd.command("create")
@inject_help(ScheduleObj)
@inject_help(Schedule)
def create_gc_schedule(
    ctx: typer.Context,
    type: Optional[ScheduleType] = typer.Option(
        None,
        "--type",
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
    ),
) -> None:
    """Create a new Garbage Collection schedule."""
    schedule_obj = ScheduleObj(
        type=type,
        cron=cron,
    )
    # TODO: investigate which parameters the `parameters` field takes
    schedule = Schedule(schedule=schedule_obj)
    state.run(
        state.client.create_gc_schedule(schedule),
        "Creating Garbage Collection schedule...",
    )
    info(f"Garbage Collection schedule created.")


@schedule_cmd.command("update")
@inject_help(ScheduleObj)
@inject_help(Schedule)
def update_gc_schedule(
    ctx: typer.Context,
    type: Optional[ScheduleType] = typer.Option(
        None,
        "--type",
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
    ),
    # NOTE: should we add ScheduleObj.next_scheduled_time as an option?
    # it doesn't seem like something that should be set manually?
    # TODO: add delete untagged artifacts option
) -> None:
    schedule = state.run(state.client.get_gc_schedule(), "Fetching current schedule...")
    if schedule.schedule is None:
        exit_err(
            "No existing schedule to update. Use `harbor gc schedule create` to create a new schedule."
        )
    # The actual schedule is stored in the `schedule` field of the `Schedule` model
    new_schedule = create_updated_model(schedule.schedule, ScheduleObj, ctx)
    schedule.schedule = new_schedule
    # TODO: investigate which parameters the `parameters` field takes
    # And whether or not that is something we can/want to update
    state.run(
        state.client.update_gc_schedule(schedule),
        f"Updating Garbage Collection schedule...",
    )
    info(f"Garbage Collection schedule updated.")


# HarborAsyncClient.get_gc_jobs()
@app.command("jobs")
@inject_resource_options()
def get_gc_jobs(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
) -> None:
    """Get garbage collection jobs."""
    check_enumeration_options(state, query=query, limit=limit)
    jobs = state.run(
        state.client.get_gc_jobs(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching Garbage Collection jobs...",
    )
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
    job = state.run(
        state.client.get_gc_job(job_id), f"Fetching Garbage Collection jobs..."
    )
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
    log_lines = state.run(
        state.client.get_gc_log(job_id, as_list=True),
        "Fetching Garbage Collection logs...",
    )
    render_result(log_lines, ctx)
