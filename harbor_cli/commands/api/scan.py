from __future__ import annotations

from pathlib import Path
from typing import List
from typing import Optional

import typer
from harborapi.models import ScanDataExportRequest

from ...harbor.artifact import parse_artifact_name
from ...logs import logger
from ...output.console import exit_err
from ...output.render import render_result
from ...state import state
from ...style import render_cli_value
from ...utils.args import construct_query_list
from ...utils.args import parse_commalist
from ...utils.args import parse_commalist_int
from ..help import ARTIFACT_HELP_STRING
from .project import get_project

app = typer.Typer(
    name="scan",
    help="Scanning of individual artifacts.",
    no_args_is_help=True,
)
export_cmd = typer.Typer(
    name="export",
    help="Export scan results.",
)
app.add_typer(export_cmd)

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


#  HarborAsyncClient.get_scan_export()
@export_cmd.command("get")
def get_scan_export(
    ctx: typer.Context,
    execution_id: int = typer.Argument(
        ..., help="The execution ID of the scan job to retrieve."
    ),
) -> None:
    """Get a specific scan export."""
    export = state.run(
        state.client.get_scan_export(execution_id), "Fetching scan export..."
    )
    render_result(export, ctx)


#  HarborAsyncClient.get_scan_exports()
@export_cmd.command("list")
def get_scan_exports(ctx: typer.Context) -> None:
    """List all scan exports for the current user."""
    exports = state.run(state.client.get_scan_exports(), "Fetching scan exports...")
    render_result(exports, ctx)


#  HarborAsyncClient.export_scan_data()
@export_cmd.command("start")
def start_scan_export(
    ctx: typer.Context,
    job_name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Custom name for export job.",
    ),
    cve: List[str] = typer.Option(
        [],
        "--cve",
        help="CVE(s) to export",
        callback=parse_commalist,
    ),
    tag: List[str] = typer.Option(
        ["**"],
        "--tag",
        help=(
            f"Multiple comma separated tags, {render_cli_value('tag*')}, or {render_cli_value('**')}. "
            "Defaults to all tags."
        ),
        callback=parse_commalist,
    ),
    label: List[str] = typer.Option(
        [],
        "--label",
        help="IDs of specific label(s) to include in the export.",
        callback=parse_commalist_int,
    ),
    repo: List[str] = typer.Option(
        ["**"],
        "--repo",
        help=(
            f"Multiple comma separated repos, {render_cli_value('repo*')}, or {render_cli_value('**')}. "
            "Defaults to all repos."
        ),
        callback=parse_commalist,
    ),
    project: List[str] = typer.Option(
        [],
        "--project",
        help="Names of project(s) to include in the export.",
        callback=parse_commalist,
    ),
    project_id: List[str] = typer.Option(
        [],
        "--project-id",
        help="IDs of project(s) to include in the export.",
        callback=parse_commalist_int,
    ),
    scan_type: str = typer.Option(
        "application/vnd.security.vulnerability.report; version=1.1",
        "--scan-type",
        help="The type of scan to export. Should not be changed unless you know what you are doing.",
    ),
) -> None:
    """Start a scan export job.

    NOTE: The official documentation for this endpoint is poor, and as such, this command might not work as intended.
    """

    # Assert for mypy that all project IDs are int + make set
    project_id_set = set([int(pid) for pid in project_id])

    # Resolve project names to IDs
    for proj in project:
        p = get_project(proj)
        if p.project_id is None:
            exit_err(f"Project {proj!r} does not have a project ID.")
        project_id_set.add(p.project_id)

    # TODO: resolve label names to IDs (?)

    req = ScanDataExportRequest()
    if job_name:
        req.job_name = job_name
    if cve:
        req.cve_ids = construct_query_list(*cve, comma=True)
    if tag:
        req.tags = construct_query_list(*tag, comma=True)
    if label:
        req.labels = label  # type: ignore
    if repo:
        req.repositories = construct_query_list(*repo, comma=True)
    if project:
        req.projects = list(project_id_set)

        export = state.run(
            state.client.export_scan_data(
                req,
                scan_type,
            ),
            "Starting scan export...",
        )
    render_result(export, ctx)


#  HarborAsyncClient.download_scan_export()
@export_cmd.command("download")
def download_scan_export(
    ctx: typer.Context,
    execution_id: int = typer.Argument(
        ...,
        help="The execution ID of the scan job to download.",
    ),
    destination: Path = typer.Argument(
        ...,
        help="Destination to download the export to. Uses application temp dir if omitted.",
    ),
) -> None:
    """Download a specific scan export."""
    export = state.run(
        state.client.download_scan_export(execution_id),
        "Downloading scan export...",
    )
    # TODO: check resp code + handle errors
    with destination.open("wb") as f:
        f.write(bytes(export))
    logger.info(f"Export downloaded to {destination!s}")
