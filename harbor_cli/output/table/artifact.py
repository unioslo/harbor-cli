from __future__ import annotations

from typing import Sequence

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models.models import Artifact
from rich.table import Table

from ..formatting.builtin import plural_str
from ..formatting.bytes import bytesize_str


def artifact_table(artifacts: Sequence[Artifact]) -> Table:
    """Display one or more repositories in a table."""
    table = Table(
        title=plural_str("Artifact", artifacts),
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID")
    table.add_column("Project ID")
    table.add_column("Repository ID")
    table.add_column("Digest", overflow="fold")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in artifacts:
        table.add_row(
            str(artifact.id),
            str(artifact.project_id),
            str(artifact.repository_id),
            artifact.digest,
            str(artifact.push_time),
            bytesize_str(artifact.size or 0),
        )
    return table


def artifactinfo_table(artifacts: Sequence[ArtifactInfo]):
    """Display one or more artifacts in a table."""
    table = Table(
        title=plural_str("Artifact", artifacts),
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Project")
    table.add_column("Repository")
    table.add_column("Tags")
    table.add_column("Digest")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in artifacts:
        table.add_row(
            str(artifact.project_name),
            str(artifact.repository_name),
            str(artifact.tags),
            str(artifact.artifact.digest),
            str(artifact.artifact.push_time),
            bytesize_str(artifact.artifact.size or 0),
        )
    return table


def artifact_vulnerabilities_table(artifact: ArtifactInfo):
    vulns = artifact.report.vulnerabilities
    table = Table(
        title=plural_str("Vulnerability", vulns),
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("CVE ID")
    table.add_column("Severity")
    table.add_column("Score")
    table.add_column("Package")
    table.add_column("Version", overflow="fold")
    table.add_column("Fix Version", overflow="fold")
    table.add_column("Description")
    for vulnerability in vulns:
        table.add_row(
            str(vulnerability.id),
            str(vulnerability.severity.value),
            str(vulnerability.get_cvss_score()),
            str(vulnerability.package),
            str(vulnerability.version),
            str(vulnerability.fix_version),
            str(vulnerability.description),
        )
    return table
