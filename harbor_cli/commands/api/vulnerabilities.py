from __future__ import annotations

from typing import Optional

import harborapi
import typer
from harborapi.ext.api import get_artifact
from harborapi.models.scanner import Severity

from ...app import app
from ...output.console import console
from ...output.console import exit_err
from ...output.format import OutputFormat
from ...output.tables import artifact_table
from ...output.tables import artifact_vulnerabilities_table
from ...state import state
from ...utils import get_artifact_parts


@app.command("vulnerabilities", no_args_is_help=True)
def vulnerabilities(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name to list vulnerabilities for.",
    ),
    repo: Optional[str] = typer.Option(
        None,
        "-r",
        "--repo",
        help="Repository name to list vulnerabilities for.",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "-t",
        "--tag",
        help="Tag name to list vulnerabilities for.",
    ),
    artifact: Optional[str] = typer.Option(
        None,
        "-a",
        "--artifact",
        help="Complete name of artifact in the form of <project>/<repo>:<tag_or_digest>",
    ),
    min_severity: Optional[Severity] = typer.Option(
        None,
        "--min-severity",
        "-s",
        help="Minimum severity of vulnerabilities to list.",
    ),
) -> None:
    # We need the parent context to get the global options (output format etc.)
    if ctx.parent is None:
        exit_err(f"No parent context found in command {ctx.command.name!r}.")

    # TODO: move to own function
    if artifact is not None:
        _, project, repo, tag_or_digest = get_artifact_parts(artifact)
        a = state.run(get_artifact(state.client, project, repo, tag_or_digest))
        try:
            a = state.loop.run_until_complete(
                get_artifact(state.client, project, repo, tag_or_digest)
                # state.client.get_artifact_vulnerabilities(project, repo, tag_or_digest)
            )
        except harborapi.exceptions.NotFound as e:  # noqa: F841
            exit_err(f"Artifact {artifact!r} not found.")
        except harborapi.exceptions.Unauthorized as e:  # noqa: F841
            # TODO: log error
            exit_err("Unauthorized. Check your credentials.")
        except harborapi.exceptions.HarborAPIException as e:
            exit_err(f"Error: {e}")

        if ctx.parent.params["output_format"] == OutputFormat.TABLE.value:
            table = artifact_table([a])
            console.print(table)

            a.report.sort(use_cvss=True)
            console.print(artifact_vulnerabilities_table(a))

        print()
