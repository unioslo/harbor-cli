from __future__ import annotations

from typing import Optional

import typer

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_resource_options

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
    retrieve_all: bool = typer.Option(True),
) -> None:
    """List audit logs for projects the current user has access to.
    [bold red]WARNING:[/] This command can return a lot of data if no query
    is specified.
    """
    logger.info(f"Fetching audit logs...")
    logs = state.run(
        state.client.get_audit_logs(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            retrieve_all=retrieve_all,
        )
    )
    render_result(logs, ctx)
