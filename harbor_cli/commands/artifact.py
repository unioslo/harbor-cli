from __future__ import annotations

from typing import Optional

import typer
from harborapi.ext.api import get_artifacts

from ..logs import logger
from ..output.console import console
from ..output.console import exit_err
from ..state import state
from ..utils import get_artifact_parts


# Create a command group
app = typer.Typer(name="artifact")


@app.command("get", no_args_is_help=True)
def get(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Name of project artifact(s) belong to.",
    ),
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Name of repository artifact(s) belong to.",
    ),
    digest: Optional[str] = typer.Option(
        None,
        "--digest",
        "-d",
        help="The digest of a specific artifact. A maximum of one artifact can be retrieved.",
    ),
    artifact: Optional[str] = typer.Option(
        None,
        "--artifact",
        "-a",
        help="The fully qualified name of a specific artifact. Overrides --project, --repo, and --digest.",
    ),
    # TODO: --tag
) -> None:
    """Get artifact(s) in a project, optionally filtered by repository.
    A single artifact can be retrieved by specifying the artifact digest as well.
    """
    # TODO: invoke --help here instead of using exit_err()
    if not any((project, repo, digest, artifact)):
        exit_err("No arguments specified. Use --help for more info.")

    logger.info(f"Fetching artifact(s)...")

    # --artifact overrides --project, --repo, and --digest
    if artifact is not None:
        domain, project, repo, digest = get_artifact_parts(artifact)

    # Get a single artifact
    # mypy: have to check for None explicitly instead of using all(...)
    if all(arg is not None for arg in (project, repo, digest)):
        # Just use normal endpoint method for a single artifact
        artifact = state.run(
            state.client.get_artifact(project, repo, digest)  # type: ignore
        )
        console.print(artifact)
        return
    # Get all artifacts in a specific repo
    elif repo is not None:
        # Use get_artifacts from harborapi.ext.api for multiple artifacts
        artifacts = state.run(
            get_artifacts(
                state.client,
                projects=[project],
                repositories=[repo],
            )
        )
        for artifactinfo in artifacts:
            console.print(artifactinfo.artifact)
        return
    # Get all artifacts in all repos in a project
    else:  # only project is specified
        artifacts = state.run(
            get_artifacts(
                state.client,
                projects=[project],
            )
        )
        for artifactinfo in artifacts:
            console.print(artifactinfo.artifact)
        return

    project_info = state.run(state.client.get_project(project))
    console.print(project_info)
