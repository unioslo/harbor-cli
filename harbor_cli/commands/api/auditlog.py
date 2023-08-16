from __future__ import annotations

from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from ...output.console import info
from ...utils.args import add_to_query
from ...utils.args import parse_commalist

if TYPE_CHECKING:
    from typing import Any  # noqa: F401

import typer
from harborapi.models import Schedule, ScheduleObj

from ...style import render_cli_option, render_cli_value

from ...output.render import render_result
from ...state import get_state
from ...utils.commands import inject_resource_options
from ...output.prompts import check_enumeration_options


state = get_state()

# Create a command group
app = typer.Typer(
    name="auditlog", help="Audit log management and access", no_args_is_help=True
)

# harbor auditlog rotation <subcommand>
rotation_cmd = typer.Typer(name="rotation", help="Log rotation", no_args_is_help=True)

# harbor auditlog rotation schedule <subcommand>
schedule_cmd = typer.Typer(
    name="schedule", help="Log rotation schedule", no_args_is_help=True
)
rotation_cmd.add_typer(schedule_cmd)

app.add_typer(rotation_cmd)


@app.command("list")
@inject_resource_options()
def list_audit_logs(
    ctx: typer.Context,
    operation: Optional[List[str]] = typer.Option(
        None,
        "--operation",
        help=f"Operation(s) to filter audit logs by. E.g. {render_cli_value('create')}.",
        callback=parse_commalist,
    ),
    resource: Optional[List[str]] = typer.Option(
        None,
        "--resource",
        help=f"Full name of the resource(s) to filter by. E.g. {render_cli_value('library/foo:latest')}.",
        callback=parse_commalist,
    ),
    resource_type: Optional[List[str]] = typer.Option(
        None,
        "--resource-type",
        help=f"Resource type(s) to filter audit logs by. E.g. {render_cli_value('artifact')}.",
        callback=parse_commalist,
    ),
    username: Optional[List[str]] = typer.Option(
        None,
        "--username",
        help=f"Username to filter audit logs by.",
        callback=parse_commalist,
    ),
    query: Optional[str] = ...,  # type: ignore
    sort: Optional[str] = ...,  # type: ignore
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = typer.Option(10),
) -> None:
    """List audit logs for projects the current user has access to.
    Recommended to specify a search query and to limit the number of results."""
    # Add syntactic sugar options to query
    query = add_to_query(
        query,
        operation=operation,
        resource=resource,
        resource_type=resource_type,
        username=username,
    )

    check_enumeration_options(state, query=query, limit=limit)
    logs = state.run(
        state.client.get_audit_logs(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching audit logs...",
    )
    render_result(logs, ctx)


# Log rotation commands


# HarborAsyncClient.get_audit_log_rotation_history()
@rotation_cmd.command("list")
@inject_resource_options()
def get_audit_log_rotation_history(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
) -> None:
    """List log rotation job logs."""
    check_enumeration_options(state, limit=limit)
    logs = state.run(
        state.client.get_audit_log_rotation_history(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching log rotation results...",
    )
    render_result(logs, ctx)


# HarborAsyncClient.get_audit_log_rotation()
@rotation_cmd.command("get")
def get_audit_log_rotation(
    ctx: typer.Context,
    job_id: int = typer.Argument(..., help="Log rotation job ID"),
) -> None:
    """Get a log rotation job."""
    result = state.run(
        state.client.get_audit_log_rotation(job_id),
        f"Fetching log rotation result...",
    )
    render_result(result, ctx)


# HarborAsyncClient.get_audit_log_rotation_log()
@rotation_cmd.command("log")
def get_audit_log_rotation_log(
    ctx: typer.Context,
    job_id: int = typer.Argument(..., help="Log rotation job ID"),
) -> None:
    """Get the log for a log rotation job."""
    status = state.run(
        state.client.get_audit_log_rotation_log(job_id),
        f"Fetching log rotation status...",
    )
    render_result(status, ctx)


# HarborAsyncClient.stop_audit_log_rotation()
@rotation_cmd.command("stop")
def stop_audit_log_rotation(
    ctx: typer.Context,
    job_id: int = typer.Argument(..., help="Log rotation job ID"),
) -> None:
    """Stop a log rotation job."""
    state.run(
        state.client.stop_audit_log_rotation(job_id),
        f"Stopping log rotation...",
    )


# HarborAsyncClient.get_audit_log_rotation_schedule()
@schedule_cmd.command("get")
def get_audit_log_rotation_schedule(
    ctx: typer.Context,
) -> None:
    """Get the log rotation schedule."""
    schedule = state.run(
        state.client.get_audit_log_rotation_schedule(),
        f"Fetching log rotation schedule...",
    )
    render_result(schedule, ctx)
    # The method returns an emtpy schedule instead of a 404 error
    # if the schedule is not set. Check the `schedule` field.
    if schedule.schedule is None:
        info("No schedule is set.")


def _get_schedule(
    cron: Optional[str],
    audit_retention_hour: Optional[int],
    include_operations: Optional[str],
    dry_run: Optional[bool],
    type: Optional[str],
) -> Schedule:
    params = {}  # type: dict[str, Any]
    if audit_retention_hour:
        params["audit_retention_hour"] = audit_retention_hour
    if dry_run:
        params["dry_run"] = dry_run
    if include_operations:
        params["include_operations"] = include_operations

    obj_kwargs = {}  # type: dict[str, Any]
    if cron:
        obj_kwargs["cron"] = cron
    if type:
        obj_kwargs["type"] = type

    return Schedule(
        parameters=params,
        schedule=ScheduleObj(**obj_kwargs),
    )


# HarborAsyncClient.create_audit_log_rotation_schedule()
@schedule_cmd.command("create")
def create_audit_log_rotation_schedule(
    ctx: typer.Context,
    type: Optional[str] = typer.Option(
        None,
        help=f"Type of schedule, e.g. {render_cli_value('Hourly')}. Mutually exclusive with {render_cli_option('--cron')}.",
    ),
    cron: Optional[str] = typer.Option(
        None, help=f"Cron expression, e.g. {render_cli_value('0 0 * * *')}"
    ),
    audit_retention_hour: Optional[int] = typer.Option(
        None,
        "--retention-hours",
        help=f"Number of hours to retain audit logs, e.g. {render_cli_value('168')}",
    ),
    # TODO: implement audit_retention_day if confirmed to work
    operations: Optional[List[str]] = typer.Option(
        None,
        help=f"Operations to rotate logs for e.g. {render_cli_value('create,delete,pull')}",
        callback=parse_commalist,
    ),
    dry_run: Optional[bool] = typer.Option(
        None,
        help="Dry run",
    ),
) -> None:
    """Create an audit log rotation schedule."""
    schedule = _get_schedule(
        cron=cron,
        audit_retention_hour=audit_retention_hour,
        include_operations=_parse_operations_args(operations),
        dry_run=dry_run,
        type=type,
    )

    s = state.run(
        state.client.create_audit_log_rotation_schedule(schedule),
        f"Creating audit log rotation schedule...",
    )
    render_result(s, ctx)


# HarborAsyncClient.update_audit_log_rotation_schedule()
@schedule_cmd.command("update")
def update_audit_log_rotation_schedule(
    ctx: typer.Context,
    type: Optional[str] = typer.Option(
        None,
        help=f"Type of schedule, e.g. {render_cli_value('Hourly')}. Mutually exclusive with {render_cli_option('--cron')}.",
    ),
    cron: Optional[str] = typer.Option(
        None, help=f"Cron expression, e.g. {render_cli_value('0 0 * * *')}"
    ),
    audit_retention_hour: Optional[int] = typer.Option(
        None,
        "--retention-hours",
        help=f"Number of hours to retain audit logs, e.g. {render_cli_value(168)}",
    ),
    operations: Optional[List[str]] = typer.Option(
        None,
        help=f"Operations to rotate logs for e.g. {render_cli_value('create,delete,pull')}",
        callback=parse_commalist,
    ),
    dry_run: Optional[bool] = typer.Option(None, help="Dry run"),
) -> None:
    """Update the audit log rotation schedule."""
    schedule = _get_schedule(
        cron=cron,
        audit_retention_hour=audit_retention_hour,
        include_operations=_parse_operations_args(operations),
        dry_run=dry_run,
        type=type,
    )

    s = state.run(
        state.client.update_audit_log_rotation_schedule(schedule),
        f"Updating audit log rotation schedule...",
    )
    render_result(s, ctx)


def _parse_operations_args(args: Optional[List[str]]) -> Optional[str]:
    # Operations is probably required, but the API spec doesn't specify that
    if not args:
        return None
    return ",".join(args)  # no spaces allowed
