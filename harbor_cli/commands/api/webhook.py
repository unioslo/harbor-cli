from __future__ import annotations

from typing import Optional

import typer

from ...output.prompts import check_enumeration_options
from ...output.render import render_result
from ...state import get_state
from ...utils.args import get_project_arg
from ...utils.commands import ARG_PROJECT_NAME_OR_ID
from ...utils.commands import inject_resource_options

state = get_state()

# Create a command group
app = typer.Typer(name="webhook", help="Manage webhooks", no_args_is_help=True)
policy_cmd = typer.Typer(
    name="policy", help="Manage webhook policies", no_args_is_help=True
)
app.add_typer(policy_cmd)


# HarborAsyncClient.get_webhook_jobs()
@app.command("jobs")
@inject_resource_options()
async def get_webhook_jobs(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    policy_id: int = typer.Argument(
        ...,
        help="ID of the webhook policy to list jobs for.",
    ),
    query: Optional[str] = ...,  # type: ignore
    sort: Optional[str] = ...,  # type: ignore
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """Get project webhook jobs for a given policy."""
    check_enumeration_options(state, query=query, limit=limit)
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(
        state.client.get_webhook_jobs(
            project_arg,
            policy_id=policy_id,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        )
    )
    render_result(result, ctx)


# HarborAsyncClient.get_webhook_policy_last_trigger()
@app.command("triggers")
def get_webhook_policy_last_trigger(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    """Get the last triggers for a webhook policy."""
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(state.client.get_webhook_policy_last_trigger(project_arg))
    render_result(result, ctx)


# HarborAsyncClient.get_webhook_supported_events()
@app.command("events", no_args_is_help=True)
def get_webhook_policy_(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    """Get the supported webhook event types."""
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(state.client.get_webhook_supported_events(project_arg))
    render_result(result, ctx)


# HarborAsyncClient.get_webhook_policies()
@policy_cmd.command("list", no_args_is_help=True)
@inject_resource_options()
def get_webhook_policies(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    query: Optional[str] = ...,  # type: ignore
    sort: Optional[str] = ...,  # type: ignore
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List webhook policies."""
    check_enumeration_options(state, query=query, limit=limit)
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(
        state.client.get_webhook_policies(
            project_arg,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        )
    )
    render_result(result, ctx)


# # HarborAsyncClient.get_webhook_policy()
@policy_cmd.command("get")
def get_webhook_policy(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    policy_id: int = typer.Option(..., help="ID of the webhook policy to get."),
) -> None:
    """Get a webhook policy."""
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(state.client.get_webhook_policy(project_arg, policy_id))
    render_result(result, ctx)


# NYI: Unknown request body format
# # HarborAsyncClient.create_webhook_policy()
# @policy_cmd.command("create")
# @inject_help(WebhookPolicy)
# def create_webhook_policy(
#     ctx: typer.Context,
#     project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
#     name: str = typer.Option(..., "--name"),
#     description: Optional[str] = typer.Option(..., "--description"),
# ) -> None:
#     pass
#  TODO: need to investigate what the API expects for the `targets` field.


# # HarborAsyncClient.update_webhook_policy()
# @policy_cmd.command("update")
# HarborAsyncClient.delete_webhook_policy()
@policy_cmd.command("delete")
def delete_webhook_policy(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    policy_id: int = typer.Option(..., help="ID of the webhook policy to delete."),
) -> None:
    """Delete a webhook policy."""
    project_arg = get_project_arg(project_name_or_id)
    result = state.run(state.client.delete_webhook_policy(project_arg, policy_id))
    render_result(result, ctx)
