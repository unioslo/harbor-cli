from __future__ import annotations

from enum import Enum
from typing import Optional

import typer
from harborapi.exceptions import NotFound
from harborapi.models.models import UserCreationReq
from harborapi.models.models import UserProfile
from harborapi.models.models import UserResp

from ...exceptions import HarborCLIError
from ...output.console import info
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...utils.args import create_updated_model
from ...utils.args import get_user_arg
from ...utils.commands import ARG_USERNAME_OR_ID
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE
from ...utils.commands import OPTION_LIMIT
from ...utils.commands import OPTION_PAGE
from ...utils.commands import OPTION_PAGE_SIZE
from ...utils.commands import OPTION_QUERY


state = get_state()

# Create a command group
app = typer.Typer(
    name="user",
    help="Manage users.",
    no_args_is_help=True,
)


# NOTE: There's way too many similar convenience functions here,
# can we combine them somehow?


def uid_from_username_or_id(username_or_id: str | int) -> int:
    """Fetches the User ID of a Harbor user given a username or ID.

    Returns the ID if it is already an integer, otherwise calls
    [uid_from_username()][harbor_cli.commands.api.user.uid_from_username]
    to fetch the ID for the given username.

    Parameters
    ----------
    username_or_id : str | int
        The username or ID of the user to fetch ID of.

    Returns
    -------
    int
        The User ID of the user.
    """
    # First, check if a command has passed the arg without parsing it itself
    # (e.g. `"id:123"` -> `123`).
    if isinstance(username_or_id, str):
        username_or_id = get_user_arg(username_or_id)

    if isinstance(username_or_id, int):
        return username_or_id
    else:
        return uid_from_username(username_or_id)


def uid_from_username(username: str) -> int:
    """Fetches the User ID of a Harbor user given a username.

    Parameters
    ----------
    username : str
        The username of the user to fetch.

    Returns
    -------
    int
        The User ID of the user.
    """
    user_resp = get_user_by_username(username)
    if user_resp.user_id is None:  # spec states ID can be None...
        raise HarborCLIError(f"User {username!r} has no user ID.")
    return user_resp.user_id


def get_user_by_username(username: str) -> UserResp:
    """Fetches a Harbor user given a username.

    Parameters
    ----------
    username : str
        The username of the user to fetch.

    Returns
    -------
    UserResp
        The user object.
    """
    try:
        user_resp = state.run(
            state.client.get_user_by_username(username), "Fetching user..."
        )
    except NotFound:
        raise HarborCLIError(f"User {username!r} not found.")
    return user_resp


def get_user_by_id(user_id: int) -> UserResp:
    """Fetches a Harbor user given a user ID.

    Parameters
    ----------
    user_id : int
        The ID of the user to fetch.

    Returns
    -------
    UserResp
        The user object.
    """
    try:
        user_resp = state.run(state.client.get_user(user_id), "Fetching user...")
    except NotFound:
        raise HarborCLIError(f"No user with ID {user_id} found.")
    return user_resp


def get_user(username_or_id: str | int) -> UserResp:
    """Fetches a Harbor user given a username or ID.

    Parameters
    ----------
    username_or_id : str | int
        The username or ID of the user to fetch.
        String arguments are treated as usernames.
        Integer arguments are treated as user IDs.

    Returns
    -------
    UserResp
        The user object.
    """
    if isinstance(username_or_id, int):
        return get_user_by_id(username_or_id)
    else:
        return get_user_by_username(username_or_id)


# HarborAsyncClient.create_user()
# There is no user object in the Harbor API schema with field descriptions
# so we can't inject help here.
@app.command("create")
def create_user(
    ctx: typer.Context,
    username: str = typer.Argument(
        ...,
        help="Username of the user to create.",
    ),
    password: Optional[str] = typer.Option(
        None,
        help="Password for user.",
    ),
    email: Optional[str] = typer.Option(
        None,
        help="Email for user.",
    ),
    realname: Optional[str] = typer.Option(
        None,
        help="Real name of user. Enclose multiple names in quotes.",
    ),
    comment: Optional[str] = typer.Option(
        None,
        help="Comment for user.",
    ),
) -> None:
    """Create a new user."""
    req = UserCreationReq(
        username=username,
        email=email,
        realname=realname,
        password=password,
        comment=comment,
    )
    user_info = state.run(state.client.create_user(req), f"Creating user...")
    render_result(user_info, ctx)
    info(f"Created user {username!r}.")


# HarborAsyncClient.update_user()
@app.command("update")
def update_user(
    ctx: typer.Context,
    username_or_id: str = ARG_USERNAME_OR_ID,
    email: Optional[str] = typer.Option(
        None,
        help="New email for the user.",
    ),
    realname: Optional[str] = typer.Option(
        None,
        help="New real name for the user.",
    ),
    comment: Optional[str] = typer.Option(
        None,
        help="New comment for the user.",
    ),
) -> None:
    """Update an existing user."""
    user = get_user(username_or_id)  # check user exists
    if user.user_id is None:
        raise HarborCLIError(
            "User Profile from API has no ID. This should never happen."
        )
    req = create_updated_model(user, UserProfile, ctx)
    state.run(state.client.update_user(user.user_id, req), "Updating user...")
    info(f"Updated user.")


# HarborAsyncClient.delete_user()
@app.command("delete")
def delete_user(
    username_or_id: str = ARG_USERNAME_OR_ID,
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a user."""
    delete_prompt(state.config, force, resource="user", name=username_or_id)
    uid = uid_from_username_or_id(username_or_id)
    state.run(state.client.delete_user(uid), "Deleting user...")
    info(f"Deleted user with ID {uid}.")


# HarborAsyncClient.search_users_by_username()
@app.command("search")
@inject_resource_options()
def search_users(
    ctx: typer.Context,
    page: int,
    page_size: int,
    limit: Optional[int],
    username: str = typer.Argument(
        ...,
        help="Username or partial username to search for.",
    ),
) -> None:
    """Search for users by username."""
    users = state.run(
        state.client.search_users_by_username(
            username,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        "Searching...",
    )
    render_result(users, ctx)


# HarborAsyncClient.set_user_admin()
@app.command("set-admin")
def set_user_admin(
    username_or_id: str = ARG_USERNAME_OR_ID,
) -> None:
    """Sets a user as admin."""
    arg = get_user_arg(username_or_id)
    uid = uid_from_username_or_id(arg)
    state.run(
        state.client.set_user_admin(uid, is_admin=True), "Setting user as admin..."
    )
    info(f"Set user with ID {uid} as admin.")


@app.command("unset-admin")
def unset_user_admin(
    username_or_id: str = ARG_USERNAME_OR_ID,
) -> None:
    """Unsets a user as admin."""
    arg = get_user_arg(username_or_id)
    uid = uid_from_username_or_id(arg)
    state.run(
        state.client.set_user_admin(uid, is_admin=False), "Removing user as admin..."
    )
    info(f"Removed user with ID {uid} as admin.")


# HarborAsyncClient.set_user_password()
@app.command("set-password")
def set_user_password(
    username_or_id: str = ARG_USERNAME_OR_ID,
    old_password: str = typer.Option(
        ...,
        "--old-password",
        prompt="Enter old password",
        hide_input=True,
        help="Old password for user. Prompted if not provided.",
    ),
    new_password: str = typer.Option(
        ...,
        "--new-password",
        prompt="Enter new password",
        hide_input=True,
        confirmation_prompt=True,
        help="New password for user. Prompted if not provided.",
    ),
) -> None:
    """Set a user's password."""
    arg = get_user_arg(username_or_id)
    uid = uid_from_username_or_id(arg)

    state.run(
        state.client.set_user_password(
            uid,
            new_password=new_password,
            old_password=old_password,
        ),
        "Setting password for user...",
    )
    info(f"Set password for user with ID {uid}.")


# HarborAsyncClient.set_user_cli_secret()
@app.command("set-cli-secret")
def set_user_cli_secret(
    username_or_id: str = ARG_USERNAME_OR_ID,
    secret: str = typer.Option(
        ...,
        help="CLI secret to set for user. If omitted, a prompt will be shown.",
        prompt="Enter CLI secret",
        hide_input=True,
        confirmation_prompt=True,
    ),
) -> None:
    """Set a user's CLI secret."""
    uid = uid_from_username_or_id(username_or_id)
    state.run(
        state.client.set_user_cli_secret(uid, secret), "Setting CLI secret for user..."
    )
    info(f"Set CLI secret for user with ID {uid}.")


# HarborAsyncClient.get_current_user()
@app.command("get-current")
def get_current_user(ctx: typer.Context) -> None:
    """Get information about the currently authenticated user."""
    user_info = state.run(state.client.get_current_user(), "Fetching current user...")
    render_result(user_info, ctx)


# HarborAsyncClient.get_current_user_permissions()
@app.command("get-current-permissions")
def get_current_user_permissions(
    ctx: typer.Context,
    scope: Optional[str] = typer.Option(
        None, "--scope", help="Scope to get permissions for."
    ),
    relative: bool = typer.Option(
        False,
        "--relative",
        help="Show permissions relative to scope.",
    ),
) -> None:
    """Get permissions for the currently authenticated user."""
    permissions = state.run(
        state.client.get_current_user_permissions(scope=scope, relative=relative),
        "Fetching current user permissions...",
    )
    # TODO: print a message here if format is table and no permissions exist?
    # it's clear when using JSON, but not so much with table
    render_result(permissions, ctx)


# HarborAsyncClient.get_user()
# HarborAsyncClient.get_user_by_username()
@app.command("get")
def get_user_command(
    ctx: typer.Context,
    username_or_id: str = ARG_USERNAME_OR_ID,
) -> None:
    """Get information about a specific user."""
    user = get_user(username_or_id)
    render_result(user, ctx)


class UserListSortMode(Enum):
    """Sort modes for the user list command."""

    ID = "id"
    USERNAME = "username"
    NAME = "name"


# HarborAsyncClient.get_users()
@app.command("list")
def list_users(
    ctx: typer.Context,
    query: Optional[str] = OPTION_QUERY,
    sort: Optional[UserListSortMode] = typer.Option(
        None,
        case_sensitive=False,
        help="Sort by field.",
    ),
    page: int = OPTION_PAGE,
    page_size: int = OPTION_PAGE_SIZE,
    limit: int = OPTION_LIMIT,
) -> None:
    """List all users in the system."""
    users = state.run(
        state.client.get_users(
            query=query,
            page=page,
            page_size=page_size,
        ),
        "Fetching users...",
    )
    if sort == UserListSortMode.ID:
        users.sort(key=lambda u: u.user_id or "")
    elif sort == UserListSortMode.USERNAME:
        users.sort(key=lambda u: u.username or "")
    elif sort == UserListSortMode.NAME:
        users.sort(key=lambda u: u.realname or "")

    if limit:
        users = users[:limit]

    render_result(users, ctx)
