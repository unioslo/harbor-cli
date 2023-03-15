from __future__ import annotations

from typing import Any
from typing import Literal
from typing import Sequence
from typing import TypedDict

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models import NativeReportSummary
from harborapi.models import VulnerabilitySummary
from harborapi.models.models import Artifact
from harborapi.models.scanner import HarborVulnerabilityReport
from rich import box
from rich.table import Table

from ...harbor.artifact import get_artifact_architecture
from ...harbor.artifact import get_artifact_native_report_summary
from ...harbor.artifact import get_artifact_severity
from ..formatting.builtin import float_str
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.bytes import bytesize_str
from ..formatting.dates import datetime_str
from ._utils import get_panel
from ._utils import get_table


def artifact_table(artifacts: Sequence[Artifact], **kwargs: Any) -> Table:
    """Display one or more artifacts in a table."""
    table = get_table("Artifact", artifacts)
    table.add_column("ID")
    table.add_column("Project ID")
    table.add_column("Repository ID")
    table.add_column("Tags")
    table.add_column("Digest", overflow="fold")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in artifacts:
        tags = []
        if artifact.tags:
            tags = [t.name for t in artifact.tags if t.name]
        t = ", ".join(tags)
        table.add_row(
            int_str(artifact.id),
            int_str(artifact.project_id),
            int_str(artifact.repository_id),
            str_str(t),
            str_str(artifact.digest),
            datetime_str(artifact.push_time),
            bytesize_str(artifact.size or 0),
        )
    return table


def artifactinfo_table(artifacts: Sequence[ArtifactInfo], **kwargs: Any):
    """Display one or more artifacts (ArtifactInfo) in a table."""
    # Pass a kwarg to display a vulnerability summary table instead
    if kwargs.get("vuln_summary", False):
        return artifactinfo_vuln_summary_table(artifacts, **kwargs)

    table = get_table("Artifact", artifacts)
    table.add_column("Project")
    table.add_column("Repository")
    table.add_column("Tags")
    table.add_column("Digest", overflow="fold")
    table.add_column("Arch")
    table.add_column("Severity")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in artifacts:
        table.add_row(
            str_str(artifact.project_name),
            str_str(artifact.repository_name),
            str_str(artifact.tags),
            str_str(artifact.artifact.digest),
            str_str(get_artifact_architecture(artifact.artifact)),
            str_str(get_artifact_severity(artifact.artifact)),
            datetime_str(artifact.artifact.push_time),
            bytesize_str(artifact.artifact.size or 0),
        )
    return table


def artifactinfo_vuln_summary_table(artifacts: Sequence[ArtifactInfo], **kwargs: Any):
    table = get_table("Artifacts")
    table.add_column("Artifact", overflow="fold")
    table.add_column("Tags", overflow="fold")
    table.add_column("Vulnerabilities", overflow="fold")

    full_digest = kwargs.pop("full_digest", False)
    for artifact in artifacts:
        name = (
            artifact.name_with_digest_full if full_digest else artifact.name_with_digest
        )
        vulns = vuln_summary_table(artifact.artifact, **kwargs)
        table.add_row(
            name,
            artifact.tags,
            vulns,
        )
    return table


def artifactinfo_panel(artifact: ArtifactInfo, **kwargs: Any):
    """Display an artifact (ArtifactInfo) in a panel.

    The vulnerabilities of the artifact are shown separately from the artifact itself."""

    artifact_table = artifactinfo_table([artifact], **kwargs)
    vuln_table = artifact_vulnerabilities_table([artifact.report], **kwargs)
    panel = get_panel([artifact_table, vuln_table], title=artifact.name_with_digest)
    return panel


def artifact_vulnerabilities_table(
    reports: Sequence[HarborVulnerabilityReport], **kwargs: Any
):
    table = get_table("Vulnerabilities", show_lines=True)
    table.add_column("CVE ID")
    table.add_column("Severity")
    table.add_column("Score")
    table.add_column("Package")
    table.add_column("Version", overflow="fold")
    table.add_column("Fix Version", overflow="fold")
    with_desc = kwargs.get("with_description", False)
    if with_desc:
        table.add_column("Description")

    # TODO: add vulnerability sorting
    for report in reports:
        vulns = report.vulnerabilities
        for vulnerability in vulns:
            row = [
                str_str(vulnerability.id),
                str_str(vulnerability.severity.value),
                float_str(vulnerability.get_cvss_score()),
                str_str(vulnerability.package),
                str_str(vulnerability.version),
                str_str(vulnerability.fix_version),
            ]
            if with_desc:
                row.append(str_str(vulnerability.description))
            table.add_row(*row)
        return table


# def scheduled_artifact_deletion_table(
#     artifacts: Sequence["ScheduledArtifactDeletion"],
# ) -> Table:
#     """Display one or more artifacts in a table."""
#     table = get_table("Scheduled Artifact Deletion", artifacts)
#     table.add_column("Artifact")
#     table.add_column("Reasons")
#     for artifact in artifacts:
#         table.add_row(
#             str_str(artifact.artifact),
#             str_str(",".join([r for r in artifact.reasons])),
#         )
#     return table


class ColKwargs(TypedDict):  # mypy complains if we use a normal dict
    min_width: int
    max_width: int
    justify: Literal["right", "left", "center"]


def vuln_summary_table(artifact: Artifact, **kwargs: Any) -> Table:
    """A single line table in the form of nC nH nM nL nU (total)
    where each letter is a color coded severity level + count.
    """
    table = Table(
        show_lines=False, show_header=False, show_edge=False, box=box.SIMPLE_HEAD
    )
    # NOTE: column is truncated if category has >9999 vulnerabilities, but that's unlikely
    col_kwargs = ColKwargs(min_width=5, max_width=5, justify="right")
    table.add_column("Critical", style="black on dark_red", **col_kwargs)
    table.add_column("High", style="black on red", **col_kwargs)
    table.add_column("Medium", style="black on orange3", **col_kwargs)
    table.add_column("Low", style="black on green", **col_kwargs)

    # not adding unknown for now
    # TODO: add kwargs toggle for this
    # table.add_column("Unknown", style="black on grey")
    table.add_column("Total")  # no style, use default (respecting theme)
    report = get_artifact_native_report_summary(artifact)
    if not report:
        report = NativeReportSummary()
    if not report.summary:
        report.summary = VulnerabilitySummary()

    table.add_row(
        f"{report.summary.critical or 0}C",
        f"{report.summary.high or 0}H",
        f"{report.summary.medium or 0}M",
        f"{report.summary.low or 0}L",
        f"({int_str(report.summary.total)})",
    )  # might include unknown?
    return table
