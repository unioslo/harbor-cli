from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models.models import Artifact
from harborapi.models.scanner import HarborVulnerabilityReport
from rich.table import Table

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
    table = get_table("Artifact", artifacts)
    table.add_column("Project")
    table.add_column("Repository")
    table.add_column("Tags")
    table.add_column("Digest", overflow="fold")
    severity = False
    if artifacts and any(a.artifact.scan_overview for a in artifacts):
        table.add_column("Severity")
        severity = True
    table.add_column("Created")
    table.add_column("Size")
    for artifact in artifacts:
        rows = [
            str_str(artifact.project_name),
            str_str(artifact.repository_name),
            str_str(artifact.tags),
            str_str(artifact.artifact.digest),
            datetime_str(artifact.artifact.push_time),
            bytesize_str(artifact.artifact.size or 0),
        ]
        if severity:
            sev = None
            if artifact.artifact.scan_overview:
                try:
                    sev = artifact.artifact.scan_overview.severity  # type: ignore
                except AttributeError:
                    pass
            rows.insert(4, str_str(sev))
        table.add_row(*rows)
    return table


def artifactinfo_panel(artifact: ArtifactInfo, **kwargs: Any):
    """Display one or more artifacts (ArtifactInfo) in a table."""

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
