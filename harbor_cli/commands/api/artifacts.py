from __future__ import annotations

from typing import Optional

import typer
from harborapi.exceptions import NotFound
from harborapi.ext.api import get_artifacts
from harborapi.models import Label
from harborapi.models import Tag

from ...logs import logger
from ...output.console import console
from ...output.console import exit
from ...output.console import exit_err
from ...output.render import render_result
from ...state import state
from ...utils import get_artifact_parts


# Create a command group
app = typer.Typer(
    name="artifacts",
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

# TODO: add callback that takes --project, --repo, --reference and --artifact
# which lets us parse it and pass it to the function via a context object

# get_artifacts()
@app.command("list")
def list_artifacts(
    ctx: typer.Context,
    project: str = typer.Argument(
        ...,
        help="Name of project to fetch artifacts from.",
    ),
    repo: str = typer.Argument(
        "",
        help="Specific repository in project to fetch artifacts from.",
    ),
    with_report: bool = typer.Option(
        False,
        "--with-report",
        "-r",
        help="Include vulnerability report in output.",
    ),
    # TODO: add ArtifactReport filtering options here
) -> None:
    """List artifacts in a project or in a specific repository."""
    if "/" in project:
        logger.info("Interpreting argument format as <project>/<repo>.")
        project, repo = project.split("/", 1)

    logger.info(f"Fetching artifact(s)...")

    # TODO: add pagination to output

    # Get all artifacts in a specific repo
    if project and repo:
        artifacts = state.run(
            get_artifacts(
                state.client,
                projects=[project],
                repositories=[repo],
            )
        )
    # Get all artifacts in all repos in a project
    else:
        artifacts = state.run(
            get_artifacts(
                state.client,
                projects=[project],
            )
        )

    render_result(artifacts, ctx)


# delete_artifact()
@app.command("delete", no_args_is_help=True)
def delete_artifact(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help="The fully qualified name of a specific artifact.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
) -> None:
    """Delete an artifact."""
    _, project, repo, reference = get_artifact_parts(artifact)
    if not force:
        if not typer.confirm(
            f"Are you sure you want to delete {artifact}?",
            abort=True,
        ):
            exit()

    logger.info(f"Deleting artifact {artifact}...")
    try:
        state.run(
            state.client.delete_artifact(project, repo, reference),
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
        help="Source artifact.",
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

    logger.info(f"Copying artifact {artifact} to {project}/{repository}...")
    try:
        resp = state.run(
            state.client.copy_artifact(project, repository, artifact),
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
        help="The fully qualified name of a specific artifact.",
    ),
    # TODO: --tag
) -> None:
    """Get artifact(s) in a project, optionally filtered by repository.
    A single artifact can be retrieved by specifying the artifact digest as well.
    """
    logger.info(f"Fetching artifact(s)...")

    _, project, repo, digest = get_artifact_parts(artifact)

    # Just use normal endpoint method for a single artifact
    artifact = state.run(
        state.client.get_artifact(project, repo, digest)  # type: ignore
    )
    render_result(artifact, ctx)


# HarborAsyncClient.get_artifact_vulnerabilities()
# HarborAsyncClient.get_artifact_build_history()
# HarborAsyncClient.get_artifact_accessories()
# HarborAsyncClient.get_artifact_tags()


@tag_cmd.command("list", no_args_is_help=True)
def list_artifact_tags(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ..., help="The fully qualified name of a specific artifact."
    ),
) -> None:
    """List tags for an artifact."""
    _, project, repo, reference = get_artifact_parts(artifact)
    tags = state.run(state.client.get_artifact_tags(project, repo, reference))

    if not tags:
        exit_err(f"No tags found for {artifact!r}")

    for tag in tags:
        console.print(tag)


# create_artifact_tag()
@tag_cmd.command("create", no_args_is_help=True)
def create_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(...),
    tag: str = typer.Argument(..., help="Name of the tag to create."),
    # signed
    # immutable
) -> None:
    """Create a tag for an artifact."""
    _, project, repo, reference = get_artifact_parts(artifact)
    # NOTE: We might need to fetch repo and artifact IDs
    t = Tag(name=tag)
    location = state.run(state.client.create_artifact_tag(project, repo, reference, t))
    logger.info(f"Created {tag} for {artifact} at {location}.")


# delete_artifact_tag()
@tag_cmd.command("delete", no_args_is_help=True)
def delete_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(...),
    tag: str = typer.Argument(..., help="Name of the tag to delete."),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation.",
    ),
) -> None:
    """Delete a tag for an artifact."""
    _, project, repo, reference = get_artifact_parts(artifact)
    # NOTE: We might need to fetch repo and artifact IDs
    if not force:
        if not typer.confirm(
            f"Are you sure you want to delete the tag {tag!r}?",
            abort=True,
        ):
            exit()

    state.run(state.client.delete_artifact_tag(project, repo, reference, tag))


# add_artifact_label()
@label_cmd.command("add", no_args_is_help=True)
def add_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help="Name of the artifact in the format '<project>/<repository><{:tag,@sha256:digest}>'.",
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
    _, project, repo, reference = get_artifact_parts(artifact)
    label = Label(
        name=name,
        description=description,
        color=color,
        scope=scope,
    )
    state.run(state.client.add_artifact_label(project, repo, reference, label))
    logger.info(f"Added label {label.name!r} to {artifact}.")


# HarborAsyncClient.delete_artifact_label()
@label_cmd.command("delete", no_args_is_help=True)
def delete_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help="Name of the artifact in the format '<project>/<repository><{:tag,@sha256:digest}>'.",
    ),
    label_id: int = typer.Argument(
        ...,
        help="ID of the label to delete.",
    ),
) -> None:
    """Add a label to an artifact."""
    _, project, repo, reference = get_artifact_parts(artifact)
    state.run(state.client.delete_artifact_label(project, repo, reference, label_id))
