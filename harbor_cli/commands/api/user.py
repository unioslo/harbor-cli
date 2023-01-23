from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import NotFound
from harborapi.models.models import UserCreationReq
from harborapi.models.models import UserProfile
from harborapi.models.models import UserResp

from ...exceptions import HarborCLIError
from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_resource_options
from ...utils.args import create_updated_model

# Create a command group
app = typer.Typer(
    name="user",
    help="Manage users.",
    no_args_is_help=True,
)


def convert_uid(uid: str | int) -> int:
    """Utility function for converting a user ID to an integer for
    commands that take a username or ID as it first argument."""
    try:
        return int(uid)
    except ValueError:
        raise HarborCLIError(
            "The first argument must be an integer ID when --id is used."
        )


def user_from_username(username: str) -> UserResp:
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
    user_resp = user_from_username(username)
    if user_resp.user_id is None:  # spec states ID can be None...
        raise HarborCLIError(f"User with username {username!r} has no user ID.")
    return user_resp.user_id


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
        help="Password of the user to create.",
    ),
    email: Optional[str] = typer.Option(
        None,
        help="Email of the user to create.",
    ),
    realname: Optional[str] = typer.Option(
        None,
        help="Real name of the user to create.",
    ),
    comment: Optional[str] = typer.Option(
        None,
        help="Comment of the user to create.",
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
    logger.info(f"Created user {username!r}.")


# HarborAsyncClient.update_user()
@app.command("update")
def update_user(
    ctx: typer.Context,
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to update. Use --id to update by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
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
    user = get_user(username_or_id, is_id)
    assert user.user_id is not None, "User ID is None"
    req = create_updated_model(user, UserProfile, ctx)
    state.run(state.client.update_user(user.user_id, req), "Updating user...")
    logger.info(f"Updated user.")


# HarborAsyncClient.delete_user()
@app.command("delete")
def delete_user(
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to delete. Use --id to delete by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt.",
    ),
) -> None:
    """Delete a user."""

    # Always confirm deletions unless --force is used
    if not force:
        typer.confirm(
            f"Are you sure you want to delete user {username_or_id!r}?",
            default=False,
            abort=True,
        )

    if is_id:
        uid = convert_uid(username_or_id)
    else:
        uid = uid_from_username(username_or_id)

    state.run(state.client.delete_user(uid), "Deleting user...")
    logger.info(f"Deleted user with ID {uid}.")


# HarborAsyncClient.search_users_by_username()
@app.command("search")
@inject_resource_options()
def search_users(
    ctx: typer.Context,
    page: int,
    page_size: int,
    retrieve_all: bool,
    username: str = typer.Argument(
        ...,
        help="Username or partial username to search for.",
    ),
) -> None:
    """Search for users by username."""
    users = state.run(
        state.client.search_users_by_username(
            username, page=page, page_size=page_size, retrieve_all=retrieve_all
        ),
        "Searching...",
    )
    render_result(users, ctx)


# HarborAsyncClient.set_user_admin()
@app.command("set-admin")
def set_user_admin(
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to set as admin. Use --id to set by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
) -> None:
    """Sets a user as admin."""
    if is_id:
        uid = convert_uid(username_or_id)
    else:
        uid = uid_from_username(username_or_id)

    state.run(
        state.client.set_user_admin(uid, is_admin=True), "Setting user as admin..."
    )
    logger.info(f"Set user with ID {uid} as admin.")


@app.command("unset-admin")
def unset_user_admin(
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to unset as admin. Use --id to set by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
) -> None:
    """Unsets a user as admin."""
    if is_id:
        uid = convert_uid(username_or_id)
    else:
        uid = uid_from_username(username_or_id)

    state.run(
        state.client.set_user_admin(uid, is_admin=False), "Removing user as admin..."
    )
    logger.info(f"Removed user with ID {uid} as admin.")


# HarborAsyncClient.set_user_password()
@app.command("set-password")
def set_user_password(
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to set password for. Use --id to set by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
    old_password: str = typer.Option(
        ...,
        "--old-password",
        prompt="Enter old password",
        hide_input=True,
        help="Old password for user.",
    ),
    new_password: str = typer.Option(
        ...,
        "--new-password",
        prompt="Enter new password",
        hide_input=True,
        confirmation_prompt=True,
        help="New password for user.",
    ),
) -> None:
    """Set a user's password."""
    if is_id:
        uid = convert_uid(username_or_id)
    else:
        uid = uid_from_username(username_or_id)

    state.run(
        state.client.set_user_password(
            uid,
            new_password=new_password,
            old_password=old_password,
        ),
        "Setting password for user...",
    )
    logger.info(f"Set password for user with ID {uid}.")


# HarborAsyncClient.set_user_cli_secret()
@app.command("set-cli-secret")
def set_user_cli_secret(
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to set CLI secret for. Use --id to set by ID.",
    ),
    secret: str = typer.Option(
        ...,
        help="CLI secret to set for user. If omitted, a prompt will be shown.",
        prompt="Enter CLI secret",
        hide_input=True,
        confirmation_prompt=True,
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
) -> None:
    """Set a user's CLI secret."""
    if is_id:
        uid = convert_uid(username_or_id)
    else:
        uid = uid_from_username(username_or_id)

    state.run(
        state.client.set_user_cli_secret(uid, secret), "Setting CLI secret for user..."
    )
    logger.info(f"Set CLI secret for user with ID {uid}.")


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
        state.client.get_current_user_permissions(),
        "Fetching current user permissions...",
    )
    # TODO: print a message here if format is table and no permissions exist?
    # it's clear when using JSON, but not so much with table
    render_result(permissions, ctx)


def get_user(username_or_id: str, is_id: bool = False) -> UserResp:
    """Get a user by username or ID."""
    msg = "Fetching user..."
    if is_id:
        uid = convert_uid(username_or_id)
        user_info = state.run(state.client.get_user(uid), msg)
    else:
        user_info = state.run(state.client.get_user_by_username(username_or_id), msg)
    return user_info


# HarborAsyncClient.get_user()
# HarborAsyncClient.get_user_by_username()
@app.command("get")
def get_user_command(
    ctx: typer.Context,
    username_or_id: str = typer.Argument(
        ...,
        help="Username or ID of user to update. Add the --id flag to update by ID.",
    ),
    is_id: bool = typer.Option(
        False,
        "--id",
        help="Argument is a user ID.",
    ),
) -> None:
    """Get information about a specific user."""
    msg = "Fetching user..."
    if is_id:
        uid = convert_uid(username_or_id)
        user_info = state.run(state.client.get_user(uid), msg)
    elif is_id is not None:
        user_info = state.run(state.client.get_user_by_username(username_or_id), msg)

    render_result(user_info, ctx)


# HarborAsyncClient.get_users()
@app.command("list")
def list_users(ctx: typer.Context) -> None:
    """List all users in the system."""
    users = state.run(state.client.get_users(), "Fetching users...")
    render_result(users, ctx)
