from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import ScannerRegistration
from harborapi.models.models import ScannerRegistrationReq

from ...output.console import info
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...utils.args import create_updated_model
from ...utils.args import model_params_from_ctx
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE

state = get_state()

# Create a command group
app = typer.Typer(
    name="scanner",
    help="Manage scanners.",
    no_args_is_help=True,
)


def get_scanner(scanner_id: str) -> ScannerRegistration:
    return state.run(state.client.get_scanner(scanner_id), "Fetching scanner...")


# HarborAsyncClient.get_scanner()
@app.command("get")
def get_csanner(
    ctx: typer.Context,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to retrieve.",
    ),
) -> None:
    """Get a specific scanner."""
    scanner = get_scanner(scanner_id)
    render_result(scanner, ctx)


# HarborAsyncClient.create_scanner()
@app.command("create", no_args_is_help=True)
@inject_help(ScannerRegistrationReq)
def create_scanner(
    ctx: typer.Context,
    name: str = typer.Argument(
        ...,
    ),
    url: str = typer.Argument(
        ...,
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
    ),
    auth: Optional[str] = typer.Option(
        None,
        "--auth",
    ),
    access_credential: Optional[str] = typer.Option(
        None,
        "--access-credential",
    ),
    skip_cert_verify: Optional[bool] = typer.Option(
        None,
        "--skip-cert-verify",
        is_flag=False,
    ),
    use_internal_addr: Optional[bool] = typer.Option(
        None,
        "--use-internal-addr",
        is_flag=False,
    ),
    disabled: Optional[bool] = typer.Option(
        None,
        "--disabled",
        is_flag=False,
    ),
) -> None:
    """Create a new scanner."""
    params = model_params_from_ctx(ctx, ScannerRegistrationReq)
    req = ScannerRegistrationReq(**params)
    location = state.run(state.client.create_scanner(req), "Creating scanner...")
    render_result(location, ctx)
    info(f"Scanner created: {location}.")


# HarborAsyncClient.update_scanner()
@app.command("update", no_args_is_help=True)
@inject_help(ScannerRegistrationReq)
def update_scanner(
    ctx: typer.Context,
    scanner_id: str = typer.Argument(..., help="ID of the scanner to update."),
    name: Optional[str] = typer.Option(
        None,
        "--name",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
    ),
    auth: Optional[str] = typer.Option(
        None,
        "--auth",
    ),
    access_credential: Optional[str] = typer.Option(
        None,
        "--access-credential",
    ),
    skip_cert_verify: Optional[bool] = typer.Option(
        None,
        "--skip-cert-verify",
        is_flag=False,
    ),
    use_internal_addr: Optional[bool] = typer.Option(
        None,
        "--use-internal-addr",
        is_flag=False,
    ),
    disabled: Optional[bool] = typer.Option(
        False,
        "--disabled",
        is_flag=False,
    ),
) -> None:
    """Update a scanner."""
    scanner = get_scanner(scanner_id)
    req = create_updated_model(scanner, ScannerRegistrationReq, ctx)

    state.run(
        state.client.update_scanner(scanner_id, req),
        "Updating scanner...",
    )
    info(f"Scanner {scanner_id!r} updated.")


# HarborAsyncClient.delete_scanner()
@app.command("delete", no_args_is_help=True)
def delete_scanner(
    ctx: typer.Context,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to delete.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a scanner."""
    delete_prompt(state.config, force, resource="scanner", name=str(scanner_id))
    state.run(state.client.delete_scanner(scanner_id), "Deleting scanner...")
    info(f"Scanner with ID {scanner_id!r} deleted.")


# HarborAsyncClient.get_scanners()
@app.command("list")
@inject_resource_options()
def list_scanners(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: int,
) -> None:
    """List scanners."""
    scanners = state.run(
        state.client.get_scanners(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching scanners...",
    )
    render_result(scanners, ctx)


# HarborAsyncClient.set_default_scanner()
@app.command("default", no_args_is_help=True)
def set_default_scanner(
    ctx: typer.Context,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to set as default.",
    ),
    unset_default: bool = typer.Option(
        False,
        "--unset",
        help="Unset the given scanner as default.",
    ),
) -> None:
    """Set/unset default scanner."""
    is_default = not unset_default  # invert the flag
    state.run(
        state.client.set_default_scanner(scanner_id, is_default),
        "Setting default scanner...",
    )
    info(f"Scanner with ID {scanner_id!r} set as default.")


# HarborAsyncClient.ping_scanner_adapter()
# TODO: verify if this is necessary or not
# could maybe be replaced by a flag in create/update
