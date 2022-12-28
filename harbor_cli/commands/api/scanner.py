from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import ScannerRegistrationReq

from ...exceptions import HarborCLIError
from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_help
from ...utils import inject_resource_options

# Create a command group
app = typer.Typer(
    name="scanner",
    help="Manage scanners.",
    no_args_is_help=True,
)


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
    logger.info(f"Fetching scanner...")
    scanner = state.run(state.client.get_scanner(scanner_id))
    render_result(scanner, ctx)


@inject_help(ScannerRegistrationReq)
def _do_handle_scanner_modification(
    ctx: typer.Context,
    scanner_id: Optional[str] = typer.Argument(
        None,
        help="ID of the scanner to modify. Ignored for create.",
    ),
    name: str = typer.Option(
        "",
        "--name",
    ),
    url: str = typer.Option(
        "",
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
        "--access-cred",
    ),
    skip_cert_verify: Optional[bool] = typer.Option(
        None,
        "--skip-cert-verify",
    ),
    use_internal_addr: Optional[bool] = typer.Option(
        None,
        "--use-internal-addr",
    ),
    disabled: bool = typer.Option(
        False,
        "--disabled",
    ),
) -> None:
    # When creating, we require
    if ctx.command.name == "create":
        if scanner_id is not None:
            raise typer.BadParameter("Unexpected argument SCANNER_ID")
        if name == "":
            raise typer.BadParameter("Missing required argument --name")
        if url == "":
            raise typer.BadParameter("Missing required argument --url")
    elif ctx.command.name == "update":
        if scanner_id is None:
            raise typer.BadParameter("Missing required argument SCANNER_ID")

    req = ScannerRegistrationReq(
        name=name,
        description=description,
        url=url,
        auth=auth,
        access_credential=access_credential,
        skip_cert_verify=skip_cert_verify,
        use_internal_addr=use_internal_addr,
        disabled=disabled,
    )
    # TODO: investigate which parameters the `parameters` field takes

    # TODO: fix this shitshow
    if ctx.command.name == "create":
        logger.info(f"Creating scanner...")
        location = state.run(state.client.create_scanner(req))
        render_result(location, ctx)
        logger.info(f"Scanner created: {location}.")
    elif ctx.command.name == "update":
        assert scanner_id is not None  # type: ignore # mypy doesn't understand that we have checked this already
        existing_scanner = state.run(state.client.get_scanner(scanner_id))
        if existing_scanner is None:
            raise HarborCLIError(f"Scanner with ID {scanner_id!r} does not exist.")
        existing_scanner.dict().update(req.dict(exclude_none=True, exclude_unset=True))
        logger.info(f"Updating scanner with ID {scanner_id!r}...")
        state.run(state.client.update_scanner(scanner_id, existing_scanner))  # type: ignore
        logger.info(f"Scanner with ID {scanner_id!r} updated.")
    else:
        raise HarborCLIError(f"Unknown command {ctx.command.name}")


# HarborAsyncClient.create_scanner()
app.command("create", help="Create a new scanner.", no_args_is_help=True)(
    _do_handle_scanner_modification
)
# HarborAsyncClient.update_scanner()
app.command("update", help="Update existing scanner.", no_args_is_help=True)(
    _do_handle_scanner_modification
)

# HarborAsyncClient.delete_scanner()
@app.command("delete", no_args_is_help=True)
def delete_scanner(
    ctx: typer.Context,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to delete.",
    ),
) -> None:
    """Delete a scanner."""
    logger.info(f"Deleting scanner...")
    state.run(state.client.delete_scanner(scanner_id))
    logger.info(f"Scanner with ID {scanner_id!r} deleted.")


# HarborAsyncClient.get_scanners()
@app.command("list")
@inject_resource_options()
def list_scanners(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
) -> None:
    """List scanners."""
    logger.info(f"Listing scanners...")
    scanners = state.run(
        state.client.get_scanners(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
        )
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
    logger.info(f"Setting default scanner...")
    is_default = not unset_default  # invert the flag
    state.run(state.client.set_default_scanner(scanner_id, is_default))
    logger.info(f"Scanner with ID {scanner_id!r} set as default.")


# HarborAsyncClient.ping_scanner_adapter()
# TODO: verify if this is necessary or not
# could maybe be replaced by a flag in create/update
