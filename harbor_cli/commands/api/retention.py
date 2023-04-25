from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import StatusError
from harborapi.models import RetentionPolicy

from ...logs import logger
from ...output.console import error
from ...output.console import exit_err
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import state
from ...style import render_cli_value
from ...utils.args import get_project_arg
from ...utils.commands import ARG_PROJECT_NAME_OR_ID_OPTIONAL
from ...utils.commands import OPTION_FORCE

app = typer.Typer(
    name="retention",
    help="Artifact retention policy management and execution.",
    no_args_is_help=True,
)
policy_app = typer.Typer(
    name="policy",
    help="Artifact retention policy.",
    no_args_is_help=True,
)
app.add_typer(policy_app)


def get_retention_policy_id(project_name_or_id: str) -> int:
    """Get the retention policy ID for a project given its name or ID."""
    arg = get_project_arg(project_name_or_id)
    policy_id = state.run(
        state.client.get_project_retention_id(arg),
        "Fetching project retention policy ID...",
    )
    if policy_id is None:
        exit_err(f"Project {render_cli_value(arg)} has no retention policy.")
    return policy_id


def get_retention_policy(policy_id: int) -> RetentionPolicy:
    """Get a retention policy given its ID."""
    return state.run(
        state.client.get_retention_policy(policy_id),
        "Fetching retention policy...",
    )


# HarborAsyncClient.get_retention_policy()
@policy_app.command("get")
def get_retention_policy_cmd(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = typer.Option(
        None,
        "--id",
        help=f"Retention policy ID. Overrides positional argument.",
    ),
) -> None:
    """Fetch a retention policy given a project name or ID, [bold]or[/bold] using a retention policy ID."""
    if policy_id is None and project_name_or_id is None:
        exit_err(f"Must provide an argument or use {render_cli_value('--id')}.")
    if project_name_or_id is not None:
        policy_id = get_retention_policy_id(project_name_or_id)

    assert policy_id is not None  # mypy...

    policy = get_retention_policy(policy_id)
    render_result(policy, ctx)


# HarborAsyncClient.delete_retention_policy()
@policy_app.command("delete")
def delete_retention_policy(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = typer.Option(
        None,
        "--id",
        help=f"Retention policy ID. Overrides positional argument.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a retention policy given a project name or ID, [bold]or[/bold] using a retention policy ID.

    NOTE: The user needs permission to update the project
    metadata in addition to managing its retention policy, due to a fatal
    API bug that will break a project if the project metadata is not updated
    after the retention policy is deleted.
    """
    if policy_id is None and project_name_or_id is None:
        exit_err(f"Must provide an argument or use {render_cli_value('--id')}.")

    if project_name_or_id is not None:
        policy_id = get_retention_policy_id(project_name_or_id)

    delete_prompt(state.config, force, resource="retention policy", name=str(policy_id))

    assert policy_id is not None  # mypy...

    # We can potentially break a project here if we are able to delete the policy
    # but not update the project's metadata, so we need to backup the project metadata,
    # so that we can restore it in case we fail to update the metadata.
    policy = get_retention_policy(policy_id)

    # Before we can delete the policy, we need to ensure we have the project ID
    # so that we can update the project metadata afterwards.
    if project_name_or_id:
        project_arg = get_project_arg(project_name_or_id)
    else:
        # get project ID from the retention policy if possible
        if policy.scope is None or policy.scope.ref is None:
            exit_err(
                "Cannot update project metadata. Unable to determine project ID from retention policy. Use the project positional argument."
            )
        project_arg = policy.scope.ref

    # Actually delete the policy
    state.run(
        state.client.delete_retention_policy(policy_id),
        "Deleting retention policy...",
    )

    # Update project metadata (if not, the project will be broken)
    try:
        state.run(
            state.client.delete_project_metadata_entry(project_arg, "retention_id"),
            "Deleting project metadata retention ID...",
            no_handle=StatusError,
        )
    except Exception:
        # TODO: ensure we are in the "correct" state (i.e. no policy but metadata exists)
        error(
            "Failed to delete project metadata retention ID. Retention policy will be restored."
        )
        state.run(
            state.client.create_retention_policy(policy),
            "Restoring retention policy...",
        )

    logger.info(f"Deleted retention policy {policy_id}.")
