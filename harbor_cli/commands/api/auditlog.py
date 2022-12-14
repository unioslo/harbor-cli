from __future__ import annotations

from typing import Optional

import typer

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_query
from ...utils import inject_sort

# Create a command group
app = typer.Typer(name="auditlog", help="System information", no_args_is_help=True)


@app.command("list")
@inject_sort()
@inject_query()
def list_audit_logs(
    ctx: typer.Context,
    query: Optional[str] = None,
    sort: Optional[str] = None,
    page_size: int = typer.Option(10, "--page-size"),
    fetch_all: bool = typer.Option(False, "--all"),
) -> None:
    """List audit logs for the current user."""
    logger.info(f"Fetching audit logs...")
    logs = state.run(
        state.client.get_audit_logs(
            query=query,
            sort=sort,
            page_size=page_size,
            retrieve_all=fetch_all,
        )
    )
    render_result(logs, ctx)
