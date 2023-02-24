from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import CVEAllowlist
from harborapi.models.models import Project
from harborapi.models.models import ProjectMetadata
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ...models import ProjectExtended
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.dates import datetime_str
from ._utils import get_table


def project_table(p: Sequence[Project], **kwargs: Any) -> Table:
    """Display one or more projects in a table."""
    table = get_table("Project", p)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Public")
    table.add_column("Repositories")
    table.add_column("Created")
    for project in p:
        table.add_row(
            str(project.name),
            str(project.project_id),
            str(project.metadata.public) if project.metadata else "Unknown",
            str(project.repo_count),
            datetime_str(project.creation_time),
        )
    return table


def project_extended_panel(p: Sequence[ProjectExtended], **kwargs: Any) -> Panel:
    """Display extended information about one or more projects."""
    if len(p) > 1:
        logger.warning("This function should only be used to display a single project.")
    pt_table = project_extended_table(p)
    pmt_table = project_metadata_table([p.metadata for p in p if p.metadata])
    # TODO: only render allowlist if allowlist is not empty
    cve_table = cveallowlist_table([p.cve_allowlist for p in p if p.cve_allowlist])
    return Panel(Group(pt_table, pmt_table, cve_table), title=p[0].name, expand=True)


def project_extended_table(p: Sequence[ProjectExtended], **kwargs: Any) -> Table:
    table = get_table(
        "Project",
        p,
        columns=[
            "ID",
            "Name",
            "Public",
            "Owner",
            "Repositories",
            "Charts",
            "Created",
        ],
    )
    for project in p:
        table.add_row(
            int_str(project.project_id),
            str_str(project.name),
            str_str(project.metadata.public) if project.metadata else "Unknown",
            str_str(project.owner_name),
            int_str(project.repo_count),
            int_str(project.chart_count),
            datetime_str(project.creation_time),
        )
    return table


def project_metadata_table(p: Sequence[ProjectMetadata], **kwargs: Any) -> Table:
    table = get_table("Project Metadata", p)
    table.add_column("Public")
    table.add_column("Content Trust")
    table.add_column("Content Trust Cosign")
    table.add_column("Vuln Prevention")
    table.add_column("Max Severity")
    table.add_column("Auto Scan")
    table.add_column("Reuse Sys CVE List")
    table.add_column("Retention ID")
    for metadata in p:
        table.add_row(
            str_str(metadata.public),
            str_str(metadata.enable_content_trust),
            str_str(metadata.enable_content_trust_cosign),
            str_str(metadata.prevent_vul),
            str_str(metadata.severity),
            str_str(metadata.auto_scan),
            str_str(metadata.reuse_sys_cve_allowlist),
            str_str(metadata.retention_id),
        )
    return table


def cveallowlist_table(c: Sequence[CVEAllowlist], **kwargs: Any) -> Table:
    table = get_table("CVE Allowlist", c)
    table.add_column("ID")
    table.add_column("Items")
    table.add_column("Expires")
    table.add_column("Created")
    table.add_column("Updated")
    for allowlist in c:
        if allowlist.items:
            items = "\n".join(
                str_str(i.cve_id) for i in allowlist.items if i is not None
            )
        else:
            items = str_str(None)

        table.add_row(
            int_str(allowlist.id),
            items,
            datetime_str(allowlist.expires_at),
            datetime_str(allowlist.creation_time),
            datetime_str(allowlist.update_time),
        )
    return table
