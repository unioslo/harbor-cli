from __future__ import annotations

import typer

from ...harbor.artifact import parse_artifact_name
from ...logs import logger
from ...output.render import render_result
from ...state import state
from ..help import ARTIFACT_HELP_STRING

# Create a command group
app = typer.Typer(
    name="scan",
    help="Scanning of individual artifacts.",
    no_args_is_help=True,
)


# HarborAsyncClient.scan_artifact()
@app.command("start")
def start_scan(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Start scanning an artifact."""
    an = parse_artifact_name(artifact)
    state.run(
        state.client.scan_artifact(an.project, an.repository, an.reference),
        "Starting artifact scan...",
    )
    logger.info(f"Scan of {artifact!r} started.")
    # TODO: add some sort of results?


# HarborAsyncClient.stop_artifact_scan()
@app.command("stop")
def stop_scan(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Stop scanning an artifact."""
    an = parse_artifact_name(artifact)
    state.run(
        state.client.stop_artifact_scan(an.project, an.repository, an.reference),
        "Stopping artifact scan...",
    )
    logger.info(f"Scan of {artifact!r} stopped.")


# HarborAsyncClient.stop_scan_all_job()
@app.command("log")
def get_artifact_scan_report_log(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    report_id: str = typer.Argument(
        ...,
        help="ID of the report to retrieve logs of.",
    ),
) -> None:
    """Get the log for a specific scan report."""
    an = parse_artifact_name(artifact)
    log = state.run(
        state.client.get_artifact_scan_report_log(
            an.project, an.repository, an.reference, report_id
        ),
        f"Fetching Artifact scan report log...",
    )
    render_result(log, ctx)
