from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import UserGroup

from ...models import UserGroupType
from ...output.console import exit_err
from ...output.console import info
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE

state = get_state()

# Create a command group
app = typer.Typer(
    name="usergroup",
    help="Manage user groups.",
    no_args_is_help=True,
)


# HarborAsyncClient.get_usergroup()
@app.command("get")
def get_usergroup(
    ctx: typer.Context,
    group_id: int = typer.Argument(..., help="ID of the group to fetch."),
) -> None:
    """Get a user group."""
    usergroup = state.run(
        state.client.get_usergroup(group_id), f"Fetching user group {group_id}..."
    )
    render_result(usergroup, ctx)


# HarborAsyncClient.create_usergroup()
@app.command("create", no_args_is_help=True)
def create_usergroup(
    ctx: typer.Context,
    group_name: str = typer.Argument(
        ...,
        help="Name of the group to create.",
    ),
    group_type: UserGroupType = typer.Argument(
        ..., help="The type of user group to create."
    ),
    ldap_group_dn: Optional[str] = typer.Option(
        None,
        "--ldap-group-dn",
        help="The DN of the LDAP group if group type is LDAP",
    ),
) -> None:
    """Create a user group."""
    if group_type == UserGroupType.LDAP and ldap_group_dn is None:
        exit_err("--ldap-group-dn is required for LDAP user groups.")

    usergroup = UserGroup(
        group_name=group_name,
        group_type=group_type.as_int(),
        ldap_group_dn=ldap_group_dn,
    )
    location = state.run(
        state.client.create_usergroup(usergroup),
        f"Creating user group {group_name}...",
    )
    render_result(location, ctx)


# HarborAsyncClient.update_usergroup()
@app.command("update")
def update_usergroup(
    group_id: int = typer.Argument(..., help="ID of the user group to update."),
    group_name: str = typer.Option(..., "--name", help="New name for the user group."),
    # NOTE: make group_name optional if we can update other fields in the future
) -> None:
    """Update a user group. Only the name can be updated currently."""
    usergroup = UserGroup(group_name=group_name)
    state.run(
        state.client.update_usergroup(group_id, usergroup),
        f"Updating user group {group_id}...",
    )
    info(f"Updated user group {group_id}.")


# HarborAsyncClient.delete_usergroup()
@app.command("delete")
def delete_usergroup(
    ctx: typer.Context,
    group_id: int = typer.Argument(..., help="ID of the user group to delete."),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a user group."""
    delete_prompt(state.config, force=force, resource="user group", name=str(group_id))
    state.run(
        state.client.delete_usergroup(group_id), f"Deleting user group {group_id}..."
    )
    info(f"Deleted user group {group_id}.")


# HarborAsyncClient.get_usergroups()
@app.command("list")
@inject_resource_options()
def get_usergroups(
    ctx: typer.Context,
    ldap_group_dn: Optional[str] = typer.Option(
        None,
        "--ldap-group-dn",
        help="LDAP group DN to filter by.",
    ),
    group_name: Optional[str] = typer.Option(
        None,
        "--group-name",
        help="Group name to filter by (fuzzy matching).",
    ),
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List user groups."""
    usergroups = state.run(
        state.client.get_usergroups(
            group_name=group_name,
            ldap_group_dn=ldap_group_dn,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        "Fetching user groups...",
    )
    render_result(usergroups, ctx)


# HarborAsyncClient.search_usergroups()
@app.command("search")
@inject_resource_options()
def search_usergroups(
    ctx: typer.Context,
    group_name: str = typer.Argument(..., help="Name of group to search for."),
    page: int = 1,
    page_size: int = 10,
    # limit: Optional[int] = ...,  # type: ignore # NYI in harborapi
) -> None:
    """Search for user groups by name."""
    usergroups = state.run(
        state.client.search_usergroups(
            group_name=group_name,
            page=page,
            page_size=page_size,
            # limit=limit,
        ),
        "Searching user groups...",
    )
    render_result(usergroups, ctx)
