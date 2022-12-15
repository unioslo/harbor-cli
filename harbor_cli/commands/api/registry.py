from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import Registry
from harborapi.models.models import RegistryCredential
from harborapi.models.models import RegistryPing
from harborapi.models.models import RegistryUpdate

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_help
from ...utils import inject_resource_options

# Create a command group
app = typer.Typer(
    name="registry",
    help="Registry management",
    no_args_is_help=True,
)


@app.command("get", no_args_is_help=True)
def get_registry(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get.",
    ),
) -> None:
    """Get information about the system."""
    logger.debug(f"Fetching registry...")
    registry = state.run(state.client.get_registry(registry_id))
    render_result(registry, ctx)


@app.command("create", no_args_is_help=True)
@inject_help(RegistryCredential)
@inject_help(Registry)
def create_registry(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        "--name",
    ),
    url: str = typer.Option(
        ...,
        "--url",
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
        None,
        "--insecure",
    ),
    description: str = typer.Option(
        None,
        "--description",
    ),
    # status omitted
) -> None:
    """Create a new registry."""
    logger.debug(f"Creating registry...")
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
    location = state.run(state.client.create_registry(registry))
    render_result(location, ctx)


@app.command("update", no_args_is_help=True)
@inject_help(RegistryUpdate)
def update_registry(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to update.",
    ),
    name: str = typer.Option(
        ...,
        "--name",
    ),
    url: str = typer.Option(
        ...,
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
    logger.debug(f"Updating registry...")
    registry = RegistryUpdate(
        name=name,
        url=url,
        description=description,
        credential_type=credential_type,
        access_key=access_key,
        access_secret=access_secret,
        insecure=insecure,
    )
    state.run(state.client.update_registry(registry_id, registry))
    render_result(None, ctx)  # is this allowed?
    logger.info("Registry updated successfully.")


@app.command("delete", no_args_is_help=True)
def delete_registry(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to delete.",
    ),
) -> None:
    """Delete a registry."""
    logger.debug(f"Deleting registry...")
    state.run(state.client.delete_registry(registry_id))
    render_result(None, ctx)
    logger.info(f"Deleted registry with ID {registry_id}.")


@app.command("info", no_args_is_help=True)
def get_registry_info(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get info for.",
    ),
) -> None:
    """Get information about a registry's triggers and resource filters"""
    logger.debug(f"Fetching registry info...")
    registry_info = state.run(state.client.get_registry_info(registry_id))
    render_result(registry_info, ctx)


@app.command("adapters", no_args_is_help=True)
def get_registry_adapters(
    ctx: typer.Context,
) -> None:
    """Get available adapters"""
    logger.debug(f"Fetching registry adapters...")
    registry_adapters = state.run(state.client.get_registry_adapters())
    render_result(registry_adapters, ctx)


@app.command("providers", no_args_is_help=True)
def get_registry_providers(
    ctx: typer.Context,
) -> None:
    """List all available registry providers"""
    logger.debug(f"Fetching registry providers...")
    registry_providers = state.run(state.client.get_registry_providers())
    render_result(registry_providers, ctx)


@app.command("status", no_args_is_help=True)
@inject_help(RegistryPing)
def check_registry_status(
    ctx: typer.Context,
    registry_id: int = typer.Argument(
        ...,
        help="ID of registry to get status of.",
    ),
) -> None:
    """Check the status of a registry. Exits with 0 if the registry is healthy, 1 otherwise."""
    # NOTE: kind of absurd calling convention, but it's what the API expects
    # maybe we just accept a registry id for now and add the other options later
    logger.debug(f"Checking registry status...")
    state.run(state.client.check_registry_status(RegistryPing(id=registry_id)))


@app.command("list")
@inject_resource_options()
def list_registries(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    retrieve_all: bool,
) -> None:
    """List all (or a subset of) registries."""
    logger.debug(f"Fetching registries..")
    registries = state.run(
        state.client.get_registries(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            retrieve_all=retrieve_all,
        )
    )
    render_result(registries, ctx)
