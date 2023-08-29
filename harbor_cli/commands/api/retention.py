from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import StatusError
from harborapi.models import RetentionPolicy

from ...output.console import error
from ...output.console import exit_err
from ...output.console import info
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...style import render_cli_value
from ...utils.args import get_project_arg
from ...utils.commands import ARG_PROJECT_NAME_OR_ID_OPTIONAL
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE

state = get_state()

app = typer.Typer(
    name="retention",
    help="Artifact retention policy management and execution.",
    no_args_is_help=True,
)
policy_cmd = typer.Typer(
    name="policy",
    help="Retention policy commands.",
    no_args_is_help=True,
)
job_cmd = typer.Typer(
    name="job",
    help="Retention job commands.",
    no_args_is_help=True,
)
task_cmd = typer.Typer(
    name="task",
    help="Retention job task commands.",
    no_args_is_help=True,
)
job_cmd.add_typer(task_cmd)  # retention job task
app.add_typer(job_cmd)  # retention job
app.add_typer(policy_cmd)  # retention policy


def policy_id_from_args(project_name_or_id: str | None, policy_id: int | None) -> int:
    """Helper function for functions that either take in a project name/id or a policy ID.
    Returns the policy ID."""
    if policy_id is None and project_name_or_id is None:
        exit_err(f"Must provide an argument or use {render_cli_value('--id')}.")

    # Policy ID takes precedence
    if policy_id is not None:
        return policy_id
    else:
        assert project_name_or_id is not None  # should be impossible to fail
        return get_retention_policy_id(project_name_or_id)


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


OPTION_POLICY_ID = typer.Option(
    None,
    "--id",
    help=f"Retention policy ID. Overrides positional argument.",
)


# HarborAsyncClient.get_retention_metadata()
@app.command("metadata")
def get_retention_metadata(ctx: typer.Context) -> None:
    """Get the metadata for retentions."""
    # NOTE: I have no idea what this does, so this description is a guess
    metadata = state.run(
        state.client.get_retention_metadata(),
        "Fetching retention metadata...",
    )
    render_result(metadata, ctx)


# HarborAsyncClient.get_retention_policy()
@policy_cmd.command("get")
def get_retention_policy_cmd(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = OPTION_POLICY_ID,
) -> None:
    """Fetch a retention policy."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    policy = get_retention_policy(policy_id)
    render_result(policy, ctx)


# HarborAsyncClient.delete_retention_policy()
@policy_cmd.command("delete")
def delete_retention_policy(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = OPTION_POLICY_ID,
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a retention policy.

    !!! warning
        The user [bold]needs[/] permission to update the project metadata
        in addition to managing its retention policy, due to a critical
        API bug that will break a project if the project metadata is not updated
        after its retention policy is deleted.
    """
    # Confirm deletion
    delete_prompt(state.config, force, resource="retention policy")

    policy_id = policy_id_from_args(project_name_or_id, policy_id)

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
                "Unable to determine project ID from retention policy. Specify project name or ID with the positional argument."
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
            "Failed to delete project metadata retention ID. Retention policy will be restored.",
            exc_info=True,
        )
        state.run(
            state.client.create_retention_policy(policy),
            "Restoring retention policy...",
        )

    info(f"Deleted retention policy {policy_id}.")


# HarborAsyncClient.get_retention_policy_id()
@policy_cmd.command("id")
def get_retention_policy_id_cmd(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
) -> None:
    """Get the retention policy ID for a project."""
    policy_id = get_retention_policy_id(project_name_or_id)
    render_result(policy_id, ctx)


# TODO: add these commands once the API is improved
# HarborAsyncClient.create_retention_policy()
# HarborAsyncClient.update_retention_policy()


# HarborAsyncClient.get_retention_executions()
@job_cmd.command("list")
@inject_resource_options()
def list_retention_jobs(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = OPTION_POLICY_ID,
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List retention jobs."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    jobs = state.run(
        state.client.get_retention_executions(
            policy_id, page=page, page_size=page_size, limit=limit
        ),
        "Fetching retention jobs...",
    )
    render_result(jobs, ctx)


# HarborAsyncClient.start_retention_execution()
@job_cmd.command("start")
@inject_resource_options()
def start_retention_job(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    policy_id: Optional[int] = OPTION_POLICY_ID,
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run job in dry run mode.",
    ),
) -> None:
    """Start a retention job."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    location = state.run(
        state.client.start_retention_execution(policy_id, dry_run),
        "Starting retention job...",
    )
    msg = f"Started retention job at {location}."
    if dry_run:
        msg += " (Dry run)"
    info(msg)


# HarborAsyncClient.stop_retention_execution()
@job_cmd.command("stop")
@inject_resource_options()
def stop_retention_job(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    job_id: int = typer.Argument(..., help="ID of the job to stop."),
    policy_id: Optional[int] = OPTION_POLICY_ID,
) -> None:
    """Stop a retention job."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    state.run(
        state.client.stop_retention_execution(policy_id, job_id),
        "Stopping retention job...",
    )
    info(f"Stopped retention job ({job_id}) for policy {policy_id}.")


# HarborAsyncClient.get_retention_tasks()
@task_cmd.command("list")
@inject_resource_options()
def list_retention_tasks(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    job_id: int = typer.Argument(..., help="ID of the job to list tasks for."),
    policy_id: Optional[int] = OPTION_POLICY_ID,
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List retention tasks."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    tasks = state.run(
        state.client.get_retention_tasks(
            policy_id, job_id, page=page, page_size=page_size, limit=limit
        ),
        "Fetching retention job tasks...",
    )
    render_result(tasks, ctx)


# HarborAsyncClient.get_retention_execution_task_log()
@task_cmd.command("log")
def get_retention_job_task_log(
    ctx: typer.Context,
    project_name_or_id: Optional[str] = ARG_PROJECT_NAME_OR_ID_OPTIONAL,
    job_id: int = typer.Argument(..., help="ID of job."),
    task_id: int = typer.Argument(..., help="ID of job task."),
    policy_id: Optional[int] = OPTION_POLICY_ID,
) -> None:
    """Get the log for a retention job task."""
    policy_id = policy_id_from_args(project_name_or_id, policy_id)
    log = state.run(
        state.client.get_retention_execution_task_log(policy_id, job_id, task_id),
        "Fetching retention job task log...",
    )
    render_result(log, ctx)
