from __future__ import annotations

from typing import Optional

import typer

from ...logs import logger
from ...output.console import console
from ...state import state

# Create a command group
app = typer.Typer(
    name="user",
    help="Manage users.",
    no_args_is_help=True,
)


# HarborAsyncClient.create_user()
# HarborAsyncClient.update_user()
# HarborAsyncClient.delete_user()
# HarborAsyncClient.get_users()
# HarborAsyncClient.search_users_by_username()
# HarborAsyncClient.set_user_admin()
# HarborAsyncClient.set_user_password()
# HarborAsyncClient.set_user_cli_secret()
# HarborAsyncClient.get_current_user()
# HarborAsyncClient.get_current_user_permissions()

# HarborAsyncClient.get_user()
# HarborAsyncClient.get_user_by_username()
@app.command("get")
def get_user(
    ctx: typer.Context,
    name: Optional[str] = typer.Option(None, "--name"),
    user_id: Optional[int] = typer.Option(None, "--user-id"),
) -> None:
    """Get information about the system."""
    if name is None and user_id is None:
        raise typer.BadParameter("Must provide either --name or --user-id")

    logger.info(f"Fetching user...")

    if name:
        logger.info(f"Fetching user {name}...")
        user_info = state.run(state.client.get_user_by_username(name))
    elif user_id is not None:
        logger.info(f"Fetching user {user_id}...")
        user_info = state.run(state.client.get_user(user_id))
    else:
        assert False, "Should not be possible"

    console.print(user_info)


@app.command("list")
def list_users(ctx: typer.Context) -> None:
    """Get information about the system volumes."""
    logger.info(f"Fetching all users...")
    users = state.run(state.client.get_users())
    console.print(users)
