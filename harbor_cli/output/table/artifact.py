from __future__ import annotations

from typing import Sequence

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models.models import Artifact
from rich.table import Table

from ..formatting.builtin import float_str
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.bytes import bytesize_str
from ..formatting.dates import datetime_str
from ._utils import get_table


def artifact_table(artifacts: Sequence[Artifact]) -> Table:
    """Display one or more repositories in a table."""
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


def artifactinfo_table(artifacts: Sequence[ArtifactInfo]):
    """Display one or more artifacts (ArtifactInfo) in a table."""
    table = table = get_table("Artifact", artifacts)
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


def artifact_vulnerabilities_table(artifact: ArtifactInfo):
    vulns = artifact.report.vulnerabilities
    table = table = get_table("Vulnerability", vulns, show_lines=True)
    table.add_column("CVE ID")
    table.add_column("Severity")
    table.add_column("Score")
    table.add_column("Package")
    table.add_column("Version", overflow="fold")
    table.add_column("Fix Version", overflow="fold")
    table.add_column("Description")
    for vulnerability in vulns:
        table.add_row(
            str_str(vulnerability.id),
            str_str(vulnerability.severity.value),
            float_str(vulnerability.get_cvss_score()),
            str_str(vulnerability.package),
            str_str(vulnerability.version),
            str_str(vulnerability.fix_version),
            str_str(vulnerability.description),
        )
    return table
