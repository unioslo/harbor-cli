from __future__ import annotations

from enum import Enum
from typing import Optional

import typer
from harborapi.models.models import ReplicationFilter
from harborapi.models.models import ReplicationPolicy
from harborapi.models.models import ReplicationTrigger
from harborapi.models.models import ReplicationTriggerSettings

from ...output.console import info
from ...output.prompts import check_enumeration_options
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...utils.args import model_params_from_ctx
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE

state = get_state()

# Create a command group
app = typer.Typer(
    name="replication",
    help="Registry replication execution and policy.",
    no_args_is_help=True,
)
policy_cmd = typer.Typer(
    name="policy",
    help="Manage replication policies.",
    no_args_is_help=True,
)
task_cmd = typer.Typer(
    name="task",
    help="Manage replication execution tasks.",
    no_args_is_help=True,
)
app.add_typer(task_cmd)
app.add_typer(policy_cmd)


# HarborAsyncClient.start_replication()
@app.command("start")
def start_replication_execution(
    ctx: typer.Context,
    policy_id: int = typer.Argument(
        ...,
        help="The ID of the policy to start a execution for.",
    ),
) -> None:
    """Start a replication execution."""
    replication_url = state.run(
        state.client.start_replication(policy_id), "Starting replication..."
    )
    render_result(replication_url, ctx)
    info(f"Replication started for policy {policy_id}.")


# HarborAsyncClient.stop_replication()
@app.command("stop")
def stop_replication_execution(
    ctx: typer.Context,
    execution_id: int = typer.Argument(
        ...,
        help="The ID of the replication execution.",
    ),
) -> None:
    """Stop a replication execution."""
    state.run(
        state.client.stop_replication(execution_id),
        f"Stopping replication execution...",
    )
    info(f"Stopped replication execution with ID {execution_id}.")


# HarborAsyncClient.get_replication()
@app.command("get")
def get_replication_execution(
    ctx: typer.Context,
    execution_id: int = typer.Argument(
        ...,
        help="The ID of the replication execution.",
    ),
) -> None:
    """Get information about a replication execution."""
    execution = state.run(
        state.client.get_replication(execution_id), "Fetching replication execution..."
    )
    render_result(execution, ctx)


# HarborAsyncClient.get_replications()
@app.command("list")
@inject_resource_options(use_defaults=False)
def list_replication_executions(
    ctx: typer.Context,
    sort: Optional[str],
    policy_id: Optional[int] = typer.Option(
        None,
        help="The ID of the policy to list executions for.",
    ),
    status: Optional[str] = typer.Option(
        None,
        help="The status of the executions to list.",
    ),
    trigger: Optional[str] = typer.Option(
        None,
        help="The trigger of the executions to list.",
    ),
    page: int = 1,
    page_size: int = 10,
    limit: Optional[int] = None,
) -> None:
    """List replication executions."""
    # treat status as the query here
    check_enumeration_options(state, query=status, limit=limit)
    executions = state.run(
        state.client.get_replications(
            sort=sort,
            trigger=trigger,
            policy_id=policy_id,
            status=status,
            page=page,
            page_size=page_size,
        ),
        "Fetching replication executions...",
    )
    render_result(executions, ctx)


# HarborAsyncClient.get_replication_policy()
@policy_cmd.command("get")
def get_replication_policy(
    ctx: typer.Context,
    policy_id: int = typer.Argument(
        ...,
        help="The ID of the replication policy.",
    ),
) -> None:
    """Get information about a replication policy."""
    policy = state.run(
        state.client.get_replication_policy(policy_id), "Fetching replication policy..."
    )
    render_result(policy, ctx)


class FilterMatchMode(Enum):
    """Filter match modes."""

    # The Web UI calls it "matching" and "excluding",
    # but the API uses the values "matches" and "excludes".
    # We follow the API naming scheme for simplicity.
    MATCHES = "matches"
    EXCLUDES = "excludes"


class FilterResourceMode(Enum):
    """Filter resource modes."""

    ALL = "all"
    IMAGE = "image"
    ARTIFACT = "artifact"


# HarborAsyncClient.create_replication_policy()
@policy_cmd.command("create")
@inject_help(ReplicationPolicy)
def create_replication_policy(
    ctx: typer.Context,
    name: str = typer.Argument(...),
    # Difference from spec: we take in the ID of registries instead of
    # the full registry definitions. In the Web UI, you can only select
    # existing registries, so this is more consistent.
    src_registry_id: int = typer.Argument(
        ...,
        help=(
            "The ID of registry to replicate from. "
            "Typically an external registry such as [green]'hub.docker.com'[/], [green]'ghcr.io'[/], etc."
        ),
    ),
    dest_registry_id: int = typer.Argument(
        ...,
        help="The ID of the registry to replicate to.",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
    ),
    dest_namespace: Optional[str] = typer.Option(
        None,
        "--dest-namespace",
    ),
    dest_namespace_replace_count: Optional[int] = typer.Option(
        None,
        "--dest-namespace-replace-count",
    ),
    replication_trigger_type: Optional[str] = typer.Option(
        None,
        "--trigger-type",
        help=ReplicationTrigger.model_fields["type"].description,
    ),
    replication_trigger_cron: Optional[str] = typer.Option(
        None,
        "--trigger-cron",
        help=ReplicationTriggerSettings.model_fields["cron"].description,
    ),
    filter_name: Optional[str] = typer.Option(
        None,
        "--filter-name",
        help=(
            "Filter the name of the resource. "
            "Leave empty or use [green]'**'[/] to match all. "
            "[green]'library/**'[/] only matches resources under [cyan]'library'[/]. "
            "For more patterns, please refer to the offical Harbor user guide."
        ),
    ),
    filter_tag: Optional[str] = typer.Option(
        None, "--filter-tag", help=("Filter the tag of the resource. ")
    ),
    filter_tag_mode: FilterMatchMode = typer.Option(
        FilterMatchMode.MATCHES.value,
        "--filter-tag-mode",
        help="Match or exclude the given tag",
    ),
    filter_label: Optional[str] = typer.Option(
        None, "--filter-label", help=("Filter the label of the resource. ")
    ),
    filter_label_mode: FilterMatchMode = typer.Option(
        FilterMatchMode.MATCHES.value,
        "--filter-label-mode",
        help="Match or exclude the given label",
    ),
    filter_resource: FilterResourceMode = typer.Option(
        FilterResourceMode.ALL.value,
        "--filter-resource",
        help="Filter the resource type to replicate.",
    ),
    replicate_deletion: Optional[bool] = typer.Option(
        None,
        "--replicate-deletion",
        is_flag=False,
    ),
    override: Optional[bool] = typer.Option(
        None,
        "--override",
        is_flag=False,
    ),
    enabled: Optional[bool] = typer.Option(
        None,
        "--enabled",
        is_flag=False,
    ),
    speed: Optional[int] = typer.Option(None, "--speed-limit"),
) -> None:
    """Create a replication policy."""
    params = model_params_from_ctx(ctx, ReplicationPolicy)

    # Get registries from API
    src_registry = state.run(state.client.get_registry(src_registry_id))
    dest_registry = state.run(state.client.get_registry(dest_registry_id))

    # Create the filter objects
    filters = []
    if filter_name:
        filters.append(
            ReplicationFilter(
                type="name",
                value=filter_name,  # type: ignore # takes Any type
                decoration=None,
            )
        )
    if filter_tag:
        filters.append(
            ReplicationFilter(
                type="tag",
                value=filter_tag,  # type: ignore # takes Any type
                decoration=filter_tag_mode.value,
            )
        )
    if filter_label:
        filters.append(
            ReplicationFilter(
                type="label",
                value=filter_label,  # type: ignore # takes Any type
                decoration=filter_label_mode.value,
            )
        )

    # create the replication policy
    policy = ReplicationPolicy(
        **params,
        trigger=ReplicationTrigger(
            type=replication_trigger_type,
            trigger_settings=ReplicationTriggerSettings(
                cron=replication_trigger_cron,
            ),
        ),
        src_registry=src_registry,
        dest_registry=dest_registry,
        filters=filters if filters else None,
    )

    policy_url = state.run(
        state.client.create_replication_policy(policy),
        f"Creating replication policy {policy}...",
    )
    info(f"Created replication policy: {policy_url}.")


# HarborAsyncClient.update_replication_policy()
# TODO: replication policy update
# It would be nice to expose the same API as create, but without the
# requirement of the source and destination registries.
# 3 options come to mind here:
#   1. Duplicate most of the code from create, but without the registry
#      arguments. This is the easiest, plays best with static analysis,
#      but is prone to errors and spec drift, since we have to maintain
#      two copies of largely the same function definitions.
#   2. Use a decorator to inject the registry arguments to a function
#      shared by both create and update. This is a bit more complex,
#      but would allow us to maintain a single function instead of two.
#      However, it would probably be a bit too "magical", and would break
#      static analysis.
#   3. Have a single monolithic function that handles both create and
#      update. This plays well with static analysis, but would also
#      require a lot of conditional logic to handle the different, and
#      sometimes conflicting, arguments. Furthermore, it would break the
#      current pattern of having a separate function for each command.
#      Users would expect `policy update`, but it would instead be
#      `policy create --update`


# HarborAsyncClient.delete_replication_policy()
@policy_cmd.command("delete")
def delete_replication_policy(
    ctx: typer.Context,
    policy_id: int = typer.Argument(
        ...,
        help="The ID of the replication policy.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a replication policy."""
    delete_prompt(
        state.config, force, resource="replication policy", name=str(policy_id)
    )
    state.run(
        state.client.delete_replication_policy(policy_id),
        f"Deleting replication policy with ID {policy_id}...",
    )
    info(f"Deleted replication policy with ID {policy_id}.")


# HarborAsyncClient.get_replication_policies()
@policy_cmd.command("list")
@inject_resource_options(use_defaults=False)
def list_replication_policies(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: int,
) -> None:
    """List replication policies."""
    policies = state.run(
        state.client.get_replication_policies(
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching replication policies...",
    )
    render_result(policies, ctx)


# Tasks


# HarborAsyncClient.get_replication_tasks()
@task_cmd.command("list")
@inject_resource_options(use_defaults=False)
def list_execution_tasks(
    ctx: typer.Context,
    sort: Optional[str],
    status: Optional[str] = typer.Option(
        None, "--status", help="Task status to filter by."
    ),
    resource_type: Optional[str] = typer.Option(
        None, "--resource-type", help="Task resource type to filter by."
    ),
    page: int = 1,
    page_size: int = 10,
    execution_id: int = typer.Argument(
        ..., help="The ID of the replication execution to list tasks for."
    ),
) -> None:
    """List replication tasks."""
    tasks = state.run(
        state.client.get_replication_tasks(
            execution_id,
            sort=sort,
            page=page,
            page_size=page_size,
            status=status,
            resource_type=resource_type,
        ),
        f"Fetching replication tasks for execution {execution_id}...",
    )
    render_result(tasks, ctx)


# HarborAsyncClient.get_replication_task_log()
@task_cmd.command("log")
def get_task_log(
    ctx: typer.Context,
    execution_id: int = typer.Argument(
        ..., help="The ID of the execution the task belongs to."
    ),
    task_id: int = typer.Argument(..., help="The ID of the task to get the log for."),
) -> None:
    """Get the log for a replication task."""
    log = state.run(
        state.client.get_replication_task_log(execution_id, task_id),
        "Fetching replication logs...",
    )
    render_result(log, ctx)
    info(
        f"Fetched log for replication task {task_id} of replication execution {execution_id}"
    )
