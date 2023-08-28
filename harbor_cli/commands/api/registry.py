from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import NotFound
from harborapi.models.models import Registry
from harborapi.models.models import RegistryCredential
from harborapi.models.models import RegistryPing
from harborapi.models.models import RegistryUpdate

from ...output.console import exit_err
from ...output.console import info
from ...output.console import success
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
    name="registry",
    help="Registry management",
    no_args_is_help=True,
)


def get_registry(registry_id: int) -> Registry:
    return state.run(state.client.get_registry(registry_id), "Fetching registry...")


@app.command("get", no_args_is_help=True)
def get_registry_cmd(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get.",
    ),
) -> None:
    """Fetch a registry."""
    registry = get_registry(registry_id)
    render_result(registry, ctx)


@app.command("create", no_args_is_help=True)
@inject_help(RegistryCredential)
@inject_help(Registry)
def create_registry(
    ctx: typer.Context,
    name: str = typer.Argument(
        ...,
    ),
    url: str = typer.Argument(
        ...,
    ),
    credential_type: str = typer.Option(
        None,
        "--credential-type",
    ),
    access_key: str = typer.Option(
        None,
        "--access-key",
    ),
    access_secret: str = typer.Option(
        None,
        "--access-secret",
    ),
    type: str = typer.Option(
        None,
        "--type",
    ),
    insecure: bool = typer.Option(
        False,
        "--insecure",
        help="Disable verification of TLS certificates.",
    ),
    description: str = typer.Option(
        None,
        "--description",
    ),
    # status omitted
) -> None:
    """Create a new registry."""
    credential = RegistryCredential(
        type=credential_type, access_key=access_key, access_secret=access_secret
    )
    registry = Registry(
        name=name,
        url=url,
        credential=credential,
        type=type,
        insecure=insecure,
        description=description,
    )
    location = state.run(state.client.create_registry(registry), "Creating registry...")
    render_result(location, ctx)


@app.command("update", no_args_is_help=True)
@inject_help(RegistryUpdate)
def update_registry(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to update.",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
    ),
    description: str = typer.Option(
        None,
        "--description",
    ),
    credential_type: str = typer.Option(
        None,
        "--credential-type",
    ),
    access_key: str = typer.Option(
        None,
        "--access-key",
    ),
    access_secret: str = typer.Option(
        None,
        "--access-secret",
    ),
    insecure: bool = typer.Option(
        None,
        "--insecure",
    ),
    # status omitted
) -> None:
    """Update a registry."""
    registry = get_registry(registry_id)
    req = create_updated_model(registry, RegistryUpdate, ctx)
    state.run(state.client.update_registry(registry_id, req), f"Updating registry...")
    info("Registry updated successfully.")


@app.command("delete", no_args_is_help=True)
def delete_registry(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to delete.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a registry."""
    delete_prompt(state.config, force, resource="registry", name=str(registry_id))
    state.run(state.client.delete_registry(registry_id), f"Deleting registry...")
    info(f"Deleted registry with ID {registry_id}.")


@app.command("info", no_args_is_help=True)
def get_registry_info(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get info for.",
    ),
) -> None:
    """Get information about a registry's triggers and resource filters"""
    registry_info = state.run(
        state.client.get_registry_info(registry_id), "Fetching registry info..."
    )
    render_result(registry_info, ctx)


@app.command("adapters")
def get_registry_adapters(
    ctx: typer.Context,
) -> None:
    """Get available adapters"""
    registry_adapters = state.run(
        state.client.get_registry_adapters(), "Fetching registry adapters..."
    )
    render_result(registry_adapters, ctx)


@app.command("providers")
def get_registry_providers(
    ctx: typer.Context,
) -> None:
    """List all available registry providers"""
    registry_providers = state.run(
        state.client.get_registry_providers(), "Fetching registry providers..."
    )
    render_result(registry_providers, ctx)


@app.command("ping", no_args_is_help=True)
@inject_help(RegistryPing)
def check_registry_status(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get status of.",
    ),
    type: Optional[str] = typer.Option(
        None,
        "--type",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
    ),
    credential_type: Optional[str] = typer.Option(
        None,
        "--credential-type",
    ),
    access_key: Optional[str] = typer.Option(
        None,
        "--access-key",
    ),
    access_secret: Optional[str] = typer.Option(
        None,
        "--access-secret",
    ),
    insecure: Optional[bool] = typer.Option(
        None,
        "--insecure",
        is_flag=False,
    ),
) -> None:
    """Ping a registry to see if it's reachable."""
    params = model_params_from_ctx(ctx, RegistryPing)
    ping = RegistryPing(id=registry_id, **params)

    # NOTE: handle all StatusErrors? or just NotFound?
    try:
        state.run(
            state.client.check_registry_status(ping),
            "Pinging registry...",
        )
    except NotFound:
        exit_err(f"Registry (id={registry_id}) not found.")
    else:
        success(f"Registry (id={registry_id}) is reachable.")


@app.command("list")
@inject_resource_options()
def list_registries(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
) -> None:
    """List registries."""
    registries = state.run(
        state.client.get_registries(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        "Fetching registries..",
    )
    render_result(registries, ctx)
