from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import NotFound
from harborapi.ext.api import get_artifact
from harborapi.ext.api import get_artifacts
from harborapi.models import Label
from harborapi.models import Tag

from ...harbor.artifact import parse_artifact_name
from ...logs import logger
from ...output.console import console
from ...output.console import exit
from ...output.console import exit_err
from ...output.render import render_result
from ...state import state
from ...utils import inject_resource_options
from ..help import ARTIFACT_HELP_STRING


# Create a command group
app = typer.Typer(
    name="artifact",
    help="Manage artifacts.",
    no_args_is_help=True,
)

# Artifact subcommands
tag_cmd = typer.Typer(
    name="tag",
    help="Artifact tag commands",
    no_args_is_help=True,
)
label_cmd = typer.Typer(
    name="label",
    help="Artifact label commands",
    no_args_is_help=True,
)

app.add_typer(tag_cmd)
app.add_typer(label_cmd)

# get_artifacts()
@app.command("list")
@inject_resource_options()
def list_artifacts(
    ctx: typer.Context,
    query: Optional[str],
    project: str = typer.Argument(
        ...,
        help="Name of project to fetch artifacts from.",
    ),
    repo: Optional[str] = typer.Argument(
        None,
        help="Specific repository in project to fetch artifacts from.",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Limit to artifacts with this tag (e.g. 'latest').",
    ),
    with_report: bool = typer.Option(
        False,
        "--with-report",
        help="Include vulnerability report in output.",
    ),
    max_connections: int = typer.Option(
        5,
        "--max-connections",
        help=(
            "Maximum number of concurrent connections to use. "
            "Setting this too high can lead to severe performance degradation."
        ),
    ),
    # TODO: add ArtifactReport filtering options here
) -> None:
    """List artifacts in a project or in a specific repository."""
    if "/" in project:
        logger.debug("Interpreting argument format as <project>/<repo>.")
        project, repo = project.split("/", 1)

    # TODO: add pagination to output

    if project and repo:
        repositories = [repo]
    else:
        repositories = None  # all repos

    artifacts = state.run(
        get_artifacts(
            state.client,
            projects=[project],
            repositories=repositories,
            tag=tag,
            query=query,
        ),
        "Fetching artifacts...",
    )
    render_result(artifacts, ctx)
    logger.info(f"Fetched {len(artifacts)} artifact(s).")


# delete_artifact()
@app.command("delete", no_args_is_help=True)
def delete_artifact(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
) -> None:
    """Delete an artifact."""
    an = parse_artifact_name(artifact)
    if not force:
        if not typer.confirm(
            f"Are you sure you want to delete {artifact}?",
            abort=True,
        ):
            exit()

    try:
        state.run(
            state.client.delete_artifact(an.project, an.repository, an.reference),
            f"Deleting artifact {artifact}...",
            no_handle=NotFound,
        )
    except NotFound:
        exit_err(f"Artifact {artifact} not found.")
    else:
        logger.info(f"Artifact {artifact} deleted.")


# copy_artifact()
@app.command("copy", no_args_is_help=True)
def copy_artifact(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    project: str = typer.Argument(
        ...,
        help="Destination project.",
    ),
    repository: str = typer.Argument(
        ...,
        help="Destination repository (without project name).",
    ),
) -> None:
    """Copy an artifact."""

    # Warn user if they pass a project name in the repository name
    # e.g. project="foo", repository="foo/bar"
    # When it should be project="foo", repository="bar"
    if project in repository:
        logger.warning(
            "Project name is part of the repository name, you likely don't want this."
        )

    try:
        resp = state.run(
            state.client.copy_artifact(project, repository, artifact),
            f"Copying artifact {artifact} to {project}/{repository}...",
            no_handle=NotFound,
        )
    except NotFound:
        exit_err(f"Artifact {artifact} not found.")
    else:
        logger.info(f"Artifact {artifact} copied to {resp}.")


# HarborAsyncClient.get_artifact()
@app.command("get")
def get(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    with_vulnerabilities: bool = typer.Option(
        False,
        "--with-vuln",
        "-v",
    ),
    # TODO: --tag
) -> None:
    """Get information about a specific artifact."""

    an = parse_artifact_name(artifact)
    # Just use normal endpoint method for a single artifact
    artifact = state.run(
        state.client.get_artifact(an.project, an.repository, an.reference),  # type: ignore
        f"Fetching artifact(s)...",
    )
    render_result(artifact, ctx)


# HarborAsyncClient.get_artifact_tags()
@tag_cmd.command("list", no_args_is_help=True)
def list_artifact_tags(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """List tags for an artifact."""
    an = parse_artifact_name(artifact)
    tags = state.run(
        state.client.get_artifact_tags(an.project, an.repository, an.reference),
        f"Fetching tags for {an!r}...",
    )

    if not tags:
        exit_err(f"No tags found for {an!r}")

    for tag in tags:
        console.print(tag)


# create_artifact_tag()
@tag_cmd.command("create", no_args_is_help=True)
def create_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    tag: str = typer.Argument(..., help="Name of the tag to create."),
    # signed
    # immutable
) -> None:
    """Create a tag for an artifact."""
    an = parse_artifact_name(artifact)
    # NOTE: We might need to fetch repo and artifact IDs
    t = Tag(name=tag)
    location = state.run(
        state.client.create_artifact_tag(an.project, an.repository, an.reference, t),
        f"Creating tag {tag!r} for {artifact}...",
    )
    logger.info(f"Created {tag!r} for {artifact}: {location}")


# delete_artifact_tag()
@tag_cmd.command("delete", no_args_is_help=True)
def delete_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    tag: str = typer.Argument(..., help="Name of the tag to delete."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
) -> None:
    """Delete a tag for an artifact."""
    an = parse_artifact_name(artifact)
    # NOTE: We might need to fetch repo and artifact IDs
    if not force:
        if not typer.confirm(
            f"Are you sure you want to delete the tag {tag!r}?",
            abort=True,
        ):
            exit()

    state.run(
        state.client.delete_artifact_tag(an.project, an.repository, an.reference, tag),
        f"Deleting tag {tag!r} for {artifact}...",
    )


# add_artifact_label()
@label_cmd.command("add", no_args_is_help=True)
def add_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Name of the label.",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Description of the label.",
    ),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Label color.",
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Scope of the label.",
    ),
) -> None:
    """Add a label to an artifact."""
    # TODO: add parameter validation. Name is probably required?
    # Otherwise, we can just leave validation to the API, and
    # print a default error message.
    an = parse_artifact_name(artifact)
    label = Label(
        name=name,
        description=description,
        color=color,
        scope=scope,
    )
    state.run(
        state.client.add_artifact_label(an.project, an.repository, an.reference, label),
        f"Adding label {label.name!r} to {artifact}...",
    )
    logger.info(f"Added label {label.name!r} to {artifact}.")


# HarborAsyncClient.delete_artifact_label()
@label_cmd.command("delete", no_args_is_help=True)
def delete_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    label_id: int = typer.Argument(
        ...,
        help="ID of the label to delete.",
    ),
) -> None:
    """Add a label to an artifact."""
    an = parse_artifact_name(artifact)
    state.run(
        state.client.delete_artifact_label(
            an.project, an.repository, an.reference, label_id
        ),
        f"Deleting label {label_id} from {artifact}...",
    )


# HarborAsyncClient.get_artifact_vulnerabilities()
# HarborAsyncClient.get_artifact_accessories()
@app.command("accessories")
def get_accessories(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Get accessories for an artifact."""
    an = parse_artifact_name(artifact)
    accessories = state.run(
        state.client.get_artifact_accessories(an.project, an.repository, an.reference),
        f"Getting accessories for {artifact}...",
    )
    render_result(accessories, ctx)


# HarborAsyncClient.get_artifact_build_history()
@app.command("buildhistory", no_args_is_help=True)
def get_buildhistory(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Get build history for an artifact."""
    an = parse_artifact_name(artifact)
    history = state.run(
        state.client.get_artifact_build_history(
            an.project, an.repository, an.reference
        ),
        f"Getting build history for {artifact}...",
    )
    render_result(history, ctx)


# harborapi.ext.api.get_artifact
@app.command("vulnerabilities")
def get_vulnerabilities(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Get vulnerabilities for an artifact."""
    an = parse_artifact_name(artifact)
    a = state.run(
        get_artifact(state.client, an.project, an.repository, an.reference),
        f"Getting vulnerabilities for {artifact}...",
    )
    render_result(a, ctx)
