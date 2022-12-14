from __future__ import annotations

import typer

from ...output.console import console
from ...state import state

# Create a command group
app = typer.Typer(
    name="project",
    help="Manage projects.",
    no_args_is_help=True,
)


@app.command("info", no_args_is_help=True)
def info(
    ctx: typer.Context,
    project: str = typer.Argument(
        ...,
        help="Project name or ID to fetch info for. Numeric strings are interpreted as IDs.",
    ),
    force_name: bool = typer.Option(
        False,
        "--force-name",
        "-n",
        help="Force project name instead of ID. Useful if project name is a number.",
    ),
) -> None:
    """Get information about a project."""
    console.print(f"Fetching project info for {project}...")
    # Interpret numeric text as project ID
    if project.isnumeric() and not force_name:
        project = int(project)  # type: ignore
    project_info = state.run(state.client.get_project(project))
    console.print(project_info)
