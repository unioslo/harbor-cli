from __future__ import annotations

from typing import Optional

import typer

from ...output.render import render_result
from ...state import state
from ...utils.commands import inject_resource_options
from ...utils.prompts import check_enumeration_options

# Create a command group
app = typer.Typer(name="auditlog", help="System information", no_args_is_help=True)


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
