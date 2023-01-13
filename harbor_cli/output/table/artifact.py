from __future__ import annotations

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models.models import Artifact
from rich.table import Table


def artifact_table(r: Artifact | list[Artifact]) -> Table:
    """Display one or more repositories in a table."""
    if isinstance(r, Artifact):
        r = [r]
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Project ID")
    table.add_column("Repository ID")
    table.add_column("Digest")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in r:
        table.add_row(
            str(artifact.id),
            str(artifact.project_id),
            str(artifact.repository_id),
            artifact.digest,
            str(artifact.push_time),
            str(artifact.size),
        )
    return table


def artifactinfo_table(a: list[ArtifactInfo] | ArtifactInfo):
    """Display one or more artifacts in a table."""
    if isinstance(a, ArtifactInfo):
        a = [a]
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Project")
    table.add_column("Repository")
    table.add_column("Tags")
    table.add_column("Digest")
    table.add_column("Created")
    table.add_column("Size")
    for artifact in a:
        table.add_row(
            artifact.project_name,
            artifact.repository_name,
            artifact.tags,
            artifact.artifact.digest,
            str(artifact.artifact.push_time),
            str(artifact.artifact.size),
        )
    return table


def artifact_vulnerabilities_table(artifact: ArtifactInfo):
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("CVE ID")
    table.add_column("Severity")
    table.add_column("Score")
    table.add_column("Package")
    table.add_column("Version", overflow="fold")
    table.add_column("Fix Version", overflow="fold")
    table.add_column("Description")
    for vulnerability in artifact.report.vulnerabilities:
        table.add_row(
            vulnerability.id,
            vulnerability.severity.value,
            str(vulnerability.get_cvss_score()),
            vulnerability.package,
            vulnerability.version,
            vulnerability.fix_version,
            vulnerability.description,
        )
    return table
