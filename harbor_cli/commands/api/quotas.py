from __future__ import annotations

from typing import List
from typing import Optional

import typer
from harborapi.models.models import QuotaUpdateReq

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_resource_options
from ...utils.args import parse_commalist

# Create a command group
app = typer.Typer(
    name="quota",
    help="Quota management",
    no_args_is_help=True,
)


@app.command("get", no_args_is_help=True)
def get_quota(
    ctx: typer.Context,
    quota_id: int = typer.Argument(
        ...,
        help="ID of quota to get.",
    ),
) -> None:
    """Fetch a quota."""
    quota = state.run(state.client.get_quota(quota_id), "Fetching quota...")
    render_result(quota, ctx)


@app.command("update", no_args_is_help=True)
def update_quota(
    ctx: typer.Context,
    quota_id: int = typer.Argument(..., help="ID of quota to update."),
    properties: List[str] = typer.Argument(
        ...,
        callback=parse_commalist,
        help=(
            "Quota properties to update in the format [green]'property=value'[/green]."
            " Multiple properties can be provided separated by spaces or commas. "
            "[red]NOTE:[/red] It is likely the property should always be [green]'storage'[/green] and the value an integer representing the quota size in bytes."
        ),
        metavar="PROP=VALUE, ...",
    )
    # status omitted
) -> None:
    """Update a registry."""
    props = {}
    for prop in properties:
        try:
            key, value = prop.split("=")
        except ValueError:
            raise typer.BadParameter(
                f"Invalid property format: {prop}. Expected format: key=value."
            )
        props[key] = value
    if not props:
        raise typer.BadParameter("No properties provided.")
    req = QuotaUpdateReq(hard=props)
    state.run(state.client.update_quota(quota_id, req), f"Updating quota...")
    render_result(req, ctx)  # is this allowed?
    logger.info("Quota updated successfully.")


@app.command("list")
@inject_resource_options()
def list_quotas(
    ctx: typer.Context,
    reference: Optional[str] = typer.Option(
        None, "--reference", help="Reference type of quotas to list."
    ),
    reference_id: Optional[str] = typer.Option(
        None, "--reference-id", help="Reference ID of quotas to list."
    ),
    sort: Optional[str] = typer.Option(
        None,
        "--sort",
        help=(
            "Sort order of quotas to list. Valid values include: "
            "[green]'hard.resource_name'[/green], "
            "[green]'-hard.resource_name'[/green], "
            "[green]'used.resource_name'[/green], "
            "[green]'-used.resource_name'[/green]."
        ),
    ),
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    retrieve_all: bool = ...,  # type: ignore
) -> None:
    """List registries."""
    registries = state.run(
        state.client.get_quotas(
            reference=reference,
            reference_id=reference_id,
            sort=sort,
            page=page,
            page_size=page_size,
            retrieve_all=retrieve_all,
        ),
        "Fetching quotas...",
    )
    render_result(registries, ctx)
