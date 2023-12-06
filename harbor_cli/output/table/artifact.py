from __future__ import annotations

import re
from typing import Any
from typing import Literal
from typing import Sequence
from typing import TypedDict

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models import BuildHistoryEntry
from harborapi.models import VulnerabilitySummary
from harborapi.models.models import Artifact
from harborapi.models.models import Tag
from harborapi.models.scanner import HarborVulnerabilityReport
from rich import box
from rich.panel import Panel
from rich.table import Table

from ...harbor.artifact import get_artifact_architecture
from ...harbor.artifact import get_artifact_severity
from ...models import ArtifactVulnerabilitySummary
from ...output.console import warning
from ...style.color import SeverityColor
from ..formatting.builtin import bool_str
from ..formatting.builtin import float_str
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.bytes import bytesize_str
from ..formatting.dates import datetime_str
from ._utils import add_column
from ._utils import get_panel
from ._utils import get_table


DOUBLE_SPACE_PATTERN = re.compile(" +")


def artifact_table(artifacts: Sequence[Artifact], **kwargs: Any) -> Table:
    """Display one or more artifacts in a table."""
    table = get_table(
        "Artifact",
        artifacts,
        columns=[
            "ID",
            "Project ID",
            "Repository ID",
            "Tags",
            "Digest",
            "Created",
            "Size",
        ],
    )
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
            str_str(artifact.digest)[:15],
            datetime_str(artifact.push_time),
            bytesize_str(artifact.size or 0),
        )
    return table


def artifactinfo_table(artifacts: Sequence[ArtifactInfo], **kwargs: Any) -> Table:
    """Display one or more artifacts (ArtifactInfo) in a table."""
    table = get_table(
        "Artifact",
        artifacts,
        columns=[
            "Project",
            "Repository",
            "Tags",
            "Digest",
            "Arch",
            "Severity",
            "Created",
            "Size",
        ],
    )
    for artifact in artifacts:
        table.add_row(
            str_str(artifact.project_name),
            str_str(artifact.repository_name),
            str_str(", ".join(artifact.tags)),
            str_str(artifact.artifact.digest)[:15],
            str_str(get_artifact_architecture(artifact.artifact)),
            str_str(get_artifact_severity(artifact.artifact)),
            datetime_str(artifact.artifact.push_time),
            bytesize_str(artifact.artifact.size or 0),
        )
    return table


def artifact_vulnerability_summary_table(
    artifacts: Sequence[ArtifactVulnerabilitySummary], **kwargs: Any
) -> Table:
    table = get_table(
        "Artifacts",
        columns=[
            "Artifact",
            "Tags",
            "Vulnerabilities",
        ],
    )

    full_digest = kwargs.pop("full_digest", False)
    for artifact in artifacts:
        if not artifact.summary or not artifact.summary.summary:
            warning(f"No summary for artifact: {artifact.artifact!r}")
            continue
        name = artifact.artifact if full_digest else artifact.artifact_short
        vulns = vuln_summary_table(artifact.summary.summary, **kwargs)
        table.add_row(
            name,
            ", ".join(artifact.tags),
            vulns,
        )
    return table


def artifactinfo_panel(artifact: ArtifactInfo, **kwargs: Any) -> Panel:
    """Display an artifact (ArtifactInfo) in a panel.

    The vulnerabilities of the artifact are shown separately from the artifact itself.
    """

    tables = []

    artifact_table = artifactinfo_table([artifact], **kwargs)
    tables.append(artifact_table)

    # Only include report if we have one
    if artifact.report.vulnerabilities:
        vuln_table = artifact_vulnerabilities_table([artifact.report], **kwargs)
        tables.append(vuln_table)

    panel = get_panel(tables, title=artifact.name_with_digest)

    return panel


def artifact_vulnerabilities_table(
    reports: Sequence[HarborVulnerabilityReport], **kwargs: Any
) -> Table:
    table = get_table(
        "Vulnerabilities",
        show_lines=True,
        columns=[
            "CVE ID",
            "Severity",
            "Score",
            "Package",
            "Version",
            "Fix Version",
        ],
    )
    with_desc = kwargs.get("with_description", False)
    if with_desc:
        add_column(table, "Description")

    # TODO: add vulnerability sorting
    for report in reports:
        report.sort()  # critical -> high -> medium -> low
        vulns = report.vulnerabilities
        for vulnerability in vulns:
            row = [
                str_str(vulnerability.id),
                SeverityColor.as_markup(vulnerability.severity.value),
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
#     table = get_table(
#         "Scheduled Artifact Deletion", artifacts, columns=["Artifact", "Reasons"]
#     )
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
    overflow: Literal["fold"]


def vuln_summary_table(summary: VulnerabilitySummary, **kwargs: Any) -> Table:
    """A single line table in the form of nC nH nM nL nU (total)
    where each letter is a color coded severity level + count.
    """
    table = Table(
        show_lines=False, show_header=False, show_edge=False, box=box.SIMPLE_HEAD
    )
    # NOTE: column is truncated if category has >9999 vulnerabilities, but that's unlikely
    col_kwargs = ColKwargs(min_width=5, max_width=5, justify="right", overflow="fold")
    table.add_column(
        "Critical", style=f"black on {SeverityColor.CRITICAL}", **col_kwargs
    )
    table.add_column("High", style=f"black on {SeverityColor.HIGH}", **col_kwargs)
    table.add_column("Medium", style=f"black on {SeverityColor.MEDIUM}", **col_kwargs)
    table.add_column("Low", style=f"black on {SeverityColor.LOW}", **col_kwargs)
    # not adding unknown for now
    # TODO: add kwargs toggle for unknown severity vulns
    table.add_column(
        "Total", overflow="fold"
    )  # no style, use default (respecting theme)

    table.add_row(
        f"{summary.critical or 0}C",
        f"{summary.high or 0}H",
        f"{summary.medium or 0}M",
        f"{summary.low or 0}L",
        f"({int_str(summary.total)})",
    )  # might include unknown?
    return table


def buildhistoryentry_table(
    history: Sequence[BuildHistoryEntry], **kwargs: Any
) -> Table:
    """Display one or more build history entries in a table.
    Omits the "author" and "empty_layer" fields.
    """
    title = _title_for_artifact("Build History", kwargs)
    table = get_table(title, columns=["Created", "Command"])
    for entry in history:
        table.add_row(
            datetime_str(entry.created),
            str_str(DOUBLE_SPACE_PATTERN.sub(" ", entry.created_by)),
        )
        table.add_section()
    return table


def tags_table(tags: Sequence[Tag], **kwargs: Any) -> Table:
    """Display one or more tags in a table."""
    title = _title_for_artifact("Tags", kwargs)
    table = get_table(title, columns=["Name", "ID", "Created", "Immutable"])
    for tag in tags:
        table.add_row(
            str_str(tag.name),
            int_str(tag.id),
            datetime_str(tag.push_time),
            bool_str(tag.immutable),
        )
    return table


def _title_for_artifact(title: str, kwargs: dict[str, Any]) -> str:
    """Adds "for <artifact>" to the title if an artifact is provided in kwargs."""
    if artifact := kwargs.get("artifact"):
        title = f"{title} for [bold]{artifact}[/bold]"
    return title
