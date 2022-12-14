from __future__ import annotations

from typing import Optional

import harborapi
import typer
from harborapi.ext.api import get_artifact
from harborapi.models.scanner import Severity

from ...app import app
from ...harbor.artifact import parse_artifact_name
from ...output.console import console
from ...output.console import exit_err
from ...output.format import OutputFormat
from ...output.tables import artifact_table
from ...output.tables import artifact_vulnerabilities_table
from ...state import state


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
    """List vulnerabilities for an artifact."""
    # TODO: move to own function
    if artifact is not None:
        an = parse_artifact_name(artifact)
        try:
            a = state.run(
                get_artifact(state.client, an.project, an.repository, an.reference)
            )
        except harborapi.exceptions.NotFound as e:  # noqa: F841
            exit_err(f"Artifact {artifact!r} not found.")
        except harborapi.exceptions.Unauthorized as e:  # noqa: F841
            # TODO: log error
            exit_err("Unauthorized. Check your credentials.")
        except harborapi.exceptions.HarborAPIException as e:
            exit_err(f"Error: {e}")
        if state.options.output_format == OutputFormat.TABLE:
            table = artifact_table([a])
            console.print(table)
            a.report.sort(use_cvss=True)
            console.print(artifact_vulnerabilities_table(a))

        print()
