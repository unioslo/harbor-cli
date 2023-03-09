from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any  # noqa: F401

import typer
from harborapi.models import Schedule, ScheduleObj

from ...style import render_cli_value

from ...output.render import render_result
from ...state import state
from ...utils.commands import inject_resource_options
from ...utils.prompts import check_enumeration_options

# Create a command group
app = typer.Typer(name="auditlog", help="System information", no_args_is_help=True)

# harbor auditlog purge <subcommand>
purge_cmd = typer.Typer(name="purge", help="Purge audit logs", no_args_is_help=True)

# harbor auditlog purge schedule <subcommand>
schedule_cmd = typer.Typer(
    name="schedule", help="Purge audit log schedule", no_args_is_help=True
)
purge_cmd.add_typer(schedule_cmd, name="schedule")

app.add_typer(purge_cmd, name="purge")


@app.command("list")
@inject_resource_options()
def list_audit_logs(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
) -> None:
    """List audit logs for projects the current user has access to.
    [bold red]WARNING:[/] This command can return a lot of data if no query or limit
    is specified.
    """
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


# Purge commands

# HarborAsyncClient.get_purge_audit_logs()
@purge_cmd.command("list")
@inject_resource_options()
def list_purge_audit_logs(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
) -> None:
    """List purge audit logs."""
    check_enumeration_options(state, limit=limit)
    logs = state.run(
        state.client.get_purge_audit_logs(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching audit log purge results...",
    )
    render_result(logs, ctx)


# HarborAsyncClient.get_purge_audit_log()
@purge_cmd.command("get")
def get_purge_audit_log(
    ctx: typer.Context,
    purge_id: int = typer.Argument(..., help="Purge audit log ID"),
) -> None:
    """Get a purge audit log job."""
    result = state.run(
        state.client.get_purge_audit_log(purge_id),
        f"Fetching audit log purge result...",
    )
    render_result(result, ctx)


# HarborAsyncClient.get_purge_audit_log_status()
@purge_cmd.command("status")
def get_purge_audit_log_status(
    ctx: typer.Context,
    purge_id: int = typer.Argument(..., help="Purge audit log ID"),
) -> None:
    """Get a purge audit log job status."""
    status = state.run(
        state.client.get_purge_audit_log_status(purge_id),
        f"Fetching audit log purge status...",
    )
    render_result(status, ctx)


# HarborAsyncClient.stop_purge_audit_log()
@purge_cmd.command("stop")
def stop_purge_audit_log(
    ctx: typer.Context,
    purge_id: int = typer.Argument(..., help="Purge audit log ID"),
) -> None:
    """Stop a purge audit log job."""
    state.run(
        state.client.stop_purge_audit_log(purge_id),
        f"Stopping audit log purge...",
    )


# HarborAsyncClient.get_purge_audit_log_schedule()
@schedule_cmd.command("get")
def get_purge_audit_log_schedule(
    ctx: typer.Context,
) -> None:
    """Get the purge audit log schedule."""
    schedule = state.run(
        state.client.get_purge_audit_log_schedule(),
        f"Fetching audit log purge schedule...",
    )
    render_result(schedule, ctx)


def _get_schedule(
    cron: Optional[str],
    audit_retention_hour: Optional[str],
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


# HarborAsyncClient.create_purge_audit_log_schedule()
@schedule_cmd.command("create")
def create_purge_audit_log_schedule(
    ctx: typer.Context,
    cron: Optional[str] = typer.Option(
        None, help=f"Cron expression, e.g. {render_cli_value('0 0 * * *')}"
    ),
    audit_retention_hour: Optional[str] = typer.Option(
        None,
        help=f"Number of hours to retain audit logs, e.g. {render_cli_value('168')}",
    ),
    include_operations: Optional[str] = typer.Option(
        None,
        help=f"Operations to purge logs for e.g. {render_cli_value('create,delete,pull')}",
    ),
    dry_run: Optional[bool] = typer.Option(None, help="Dry run"),
    type: Optional[str] = typer.Option(
        None, help=f"Type of schedule, e.g. {render_cli_value('Hourly')}."
    ),
) -> None:
    """Create a purge audit log schedule."""
    schedule = _get_schedule(
        cron=cron,
        audit_retention_hour=audit_retention_hour,
        include_operations=include_operations,
        dry_run=dry_run,
        type=type,
    )

    s = state.run(
        state.client.create_purge_audit_log_schedule(schedule),
        f"Creating audit log purge schedule...",
    )
    render_result(s, ctx)


# HarborAsyncClient.update_purge_audit_log_schedule()
@schedule_cmd.command("update")
def update_purge_audit_log_schedule(
    ctx: typer.Context,
    cron: Optional[str] = typer.Option(
        None, help=f"Cron expression, e.g. {render_cli_value('0 0 * * *')}"
    ),
    audit_retention_hour: Optional[str] = typer.Option(
        None,
        help=f"Number of hours to retain audit logs, e.g. {render_cli_value('168')}",
    ),
    include_operations: Optional[str] = typer.Option(
        None,
        help=f"Operations to purge logs for e.g. {render_cli_value('create,delete,pull')}",
    ),
    dry_run: Optional[bool] = typer.Option(None, help="Dry run"),
    type: Optional[str] = typer.Option(
        None, help=f"Type of schedule, e.g. {render_cli_value('Hourly')}."
    ),
) -> None:
    schedule = _get_schedule(
        cron=cron,
        audit_retention_hour=audit_retention_hour,
        include_operations=include_operations,
        dry_run=dry_run,
        type=type,
    )

    s = state.run(
        state.client.update_purge_audit_log_schedule(schedule),
        f"Creating audit log purge schedule...",
    )
    render_result(s, ctx)
