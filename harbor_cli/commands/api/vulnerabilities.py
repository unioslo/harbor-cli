from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.scanner import Severity

from ...app import app


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
    raise NotImplementedError("Disabled for now.")
