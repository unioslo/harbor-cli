from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import Repository

from ...output.console import info
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE


state = get_state()

# Create a command group
app = typer.Typer(
    name="repository",
    help="Manage repositories.",
    no_args_is_help=True,
)


def get_repository(project: str, repository_name: str) -> Repository:
    return state.run(
        state.client.get_repository(project, repository_name),
        "Fetching repository...",
    )


# HarborAsyncClient.get_repository()
@app.command("get", no_args_is_help=True)
def get_reposity_command(
    ctx: typer.Context,
    project: str = typer.Argument(
        ...,
        help="Name of the project the repository belongs to.",
    ),
    repository: str = typer.Argument(
        ...,
        help="Name of the repository to get.",
    ),
) -> None:
    """Fetch a repository."""
    # TODO: accept single arg like in `harbor-cli artifact get`?
    repo = get_repository(project, repository)
    render_result(repo, ctx)


# HarborAsyncClient.delete_repository()
@app.command("delete", no_args_is_help=True)
def delete_artifact(
    ctx: typer.Context,
    project: str = typer.Argument(
        ...,
        help="Name of the project the repository belongs to.",
    ),
    repository: str = typer.Argument(
        ...,
        help="Name of the repository to get.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a repository."""
    delete_prompt(
        state.config, force, resource="repository", name=f"{project}/{repository}"
    )
    state.run(
        state.client.delete_repository(
            project,
            repository,
        ),
        "Deleting repository...",
    )
    info(f"Deleted {project}/{repository}.")


# HarborAsyncClient.update_repository()
@app.command("update")
@inject_help(Repository)
def update_repository(
    ctx: typer.Context,
    project: str = typer.Argument(
        ...,
        help="Project name of repository to update.",
    ),
    repository: str = typer.Argument(
        ...,
        help="Name of the repository to update.",
    ),
    description: Optional[str] = typer.Option(None),
) -> None:
    """Update a repository.

    As of now, only the description can be updated (if the Web UI is to be trusted).
    """
    repo = get_repository(project, repository)
    repo.description = description
    state.run(state.client.update_repository(project, repository, repo))
    info(f"Updated {project}/{repository}.")


# HarborAsyncClient.get_repositories()
@app.command("list")
@inject_resource_options()
def list_repos(
    ctx: typer.Context,
    project: Optional[str] = typer.Argument(
        None,
        help="Name of project to fetch repositories from. If not specified, all projects will be searched.",
    ),
    query: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List repositories in all projects or a specific project."""

    repos = state.run(
        state.client.get_repositories(
            project,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        "Fetching repositories...",
    )
    render_result(repos, ctx)
