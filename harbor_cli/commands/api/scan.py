from __future__ import annotations

from pathlib import Path
from typing import List
from typing import Optional

import typer
from harborapi.models import ScanDataExportRequest

from ...harbor.artifact import parse_artifact_name
from ...output.console import info
from ...output.render import render_result
from ...state import get_state
from ...style import render_cli_value
from ...style.style import render_cli_command
from ...utils.args import construct_query_list
from ...utils.args import parse_commalist
from ...utils.args import parse_commalist_int
from ..help import ARTIFACT_HELP_STRING
from .project import get_project

state = get_state()

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
    info(f"Scan of {artifact!r} started.")
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
    info(f"Scan of {artifact!r} stopped.")


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


export_start_help = f"""Start a scan export job.

Returns an execution ID that can be used to download the export once it is finished
using {render_cli_command('harbor scan export download')}

!!! warning
    The official documentation for this endpoint is poor, and as such, this command might not work as intended."""


#  HarborAsyncClient.export_scan_data()
@export_cmd.command("start", help=export_start_help)
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
            f"Names of tag(s) to include in the export. "
            f"Supports wildcards ({render_cli_value('tag*')}, {render_cli_value('**')}). "
            f"Defaults to all tags ({render_cli_value('**')})"
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
            f"Names of repo(s) to include in the export. "
            f"Supports wildcards ({render_cli_value('repo*')}, {render_cli_value('**')}). "
            f"Defaults to all repos ({render_cli_value('**')})"
        ),
        callback=parse_commalist,
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Name or ID of project to include in the export.",
    ),
    scan_type: str = typer.Option(
        "application/vnd.security.vulnerability.report; version=1.1",
        "--scan-type",
        help="The type of scan to export. Should not be changed unless you know what you are doing.",
    ),
) -> None:
    # TODO: resolve label names to IDs (?)

    req = ScanDataExportRequest()
    if job_name:
        req.job_name = job_name
    if cve:
        req.cve_ids = construct_query_list(*cve, comma=True)
    # TODO: investigate if tags should be comma-separated or not
    if tag:
        req.tags = construct_query_list(*tag, comma=True)
    if label:
        req.labels = label  # type: ignore
    # TODO: investigate if tags should be comma-separated or not
    if repo:
        req.repositories = construct_query_list(*repo, comma=True)
    if project is not None:
        # Resolve project names to IDs
        p = get_project(project)
        assert p.project_id is not None, f"Project {project!r} has no ID"
        req.projects = [p.project_id]

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
        help="Destination to download the export to.",
        # TODO: use automatic filename if omitted
        # Which location do we save to?
    ),
) -> None:
    """Download the results of a scan export job as a CSV file."""
    export = state.run(
        state.client.download_scan_export(execution_id),
        "Downloading scan export...",
    )
    # TODO: check resp code + handle errors
    with destination.open("wb") as f:
        f.write(bytes(export))
    info(f"Export downloaded to {destination!s}")
