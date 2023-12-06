from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import Project
from harborapi.models.models import ProjectMetadata
from harborapi.models.models import ProjectReq
from harborapi.models.models import ProjectSummary
from harborapi.models.models import ProjectSummaryQuota
from harborapi.models.models import ResourceList
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ...models import ProjectCreateResult
from ...models import ProjectExtended
from ..console import error
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.bytes import bytesize_str
from ..formatting.dates import datetime_str
from ..formatting.harbor import boolstr_str
from ._utils import get_panel
from ._utils import get_table
from .cve import cveallowlist_table
from .registry import registry_table


def project_table(p: Sequence[Project], **kwargs: Any) -> Table:
    """Display one or more projects in a table."""
    table = get_table(
        "Project",
        p,
        columns=[
            "ID",
            "Name",
            "Public",
            "Repositories",
            "Created",
        ],
    )
    for project in p:
        # TODO: handle ProjectMetadata fields that can be `'true'`, `'false'`, or `None`
        # Other tables can use bool_str, but here we need to handle strings
        table.add_row(
            str(project.project_id),
            str(project.name),
            boolstr_str(project.metadata.public) if project.metadata else "Unknown",
            str(project.repo_count),
            datetime_str(project.creation_time),
        )
    return table


def project_extended_panel(p: Sequence[ProjectExtended], **kwargs: Any) -> Panel:
    """Display extended information about one or more projects."""
    if len(p) != 1:
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
            "Owner",
            "Repositories",
            "Created",
        ],
    )
    for project in p:
        table.add_row(
            int_str(project.project_id),
            str_str(project.name),
            str_str(project.owner_name),
            int_str(project.repo_count),
            datetime_str(project.creation_time),
        )
    return table


def project_metadata_table(p: Sequence[ProjectMetadata], **kwargs: Any) -> Table:
    table = get_table(
        "Metadata",
        p,
        columns=[
            "Public",
            "Content Trust",
            "Content Trust Cosign",
            "Vuln Prevention",
            "Max Severity",
            "Auto Scan",
            "Reuse Sys CVE List",
            "Retention ID",
        ],
    )
    for metadata in p:
        table.add_row(
            boolstr_str(metadata.public),
            boolstr_str(metadata.enable_content_trust),
            boolstr_str(metadata.enable_content_trust_cosign),
            boolstr_str(metadata.prevent_vul),
            str_str(metadata.severity),
            boolstr_str(metadata.auto_scan),
            boolstr_str(metadata.reuse_sys_cve_allowlist),
            str_str(str(metadata.retention_id)),
        )
    return table


def _get_quota(resource: ResourceList | None) -> int | None:
    try:
        quota = resource.storage  # type: ignore
        if quota is not None:
            # NOTE: try to convert to int in case this is a float or string?
            assert isinstance(quota, int)
    except (AttributeError, AssertionError) as e:
        if isinstance(e, AssertionError):
            error(f"Resource quota is not an integer: {quota}")
        quota = None
    return quota


def project_summary_panel(p: ProjectSummary, **kwargs: Any) -> Panel:
    """Panel showing summary of a project."""
    tables = []  # type: list[Table]
    counts_table = get_table(
        columns=[
            "Repos",
            "Admins",
            "Maintainers",
            "Developers",
            "Guests",
            "Limited Guests",
        ],
    )
    counts_table.add_row(
        # Makes no sense that some fields can be None and others 0,
        # so we make them all 0 if they are None.
        int_str(p.repo_count or 0),
        int_str(p.project_admin_count or 0),
        int_str(p.maintainer_count or 0),
        int_str(p.developer_count or 0),
        int_str(p.guest_count or 0),
        int_str(p.limited_guest_count or 0),
    )

    tables.append(counts_table)

    if p.quota:
        quota_table = project_summary_quota_table(p.quota)
        tables.append(quota_table)

    # TODO: ensure this actually works. None of our test projects have registries.
    if p.registry:
        reg_table = registry_table([p.registry])
        tables.append(reg_table)

    return get_panel(tables, title=kwargs.get("project_name", None))


def project_summary_quota_table(p: ProjectSummaryQuota, **kwargs: Any) -> Table:
    table = get_table("Quota", columns=["Limit", "Used"])
    limit = _get_quota(p.hard)

    table.add_row(
        bytesize_str(limit),
        bytesize_str(_get_quota(p.used) or 0),
    )
    return table


def project_req_table(p: ProjectReq, **kwargs: Any) -> Table:
    table = get_table(
        "Project",
        columns=["Name", "Storage Limit", "Registry ID"],
    )
    table.add_row(
        str_str(p.project_name),
        bytesize_str(p.storage_limit),
        int_str(p.registry_id),
    )
    return table


def project_create_result_panel(p: ProjectCreateResult, **kwargs: Any) -> Panel:
    """Display extended information about one or more projects."""
    tables = []
    pt_table = project_req_table(p.project)
    tables.append(pt_table)
    if p.project.metadata:
        tables.append(project_metadata_table([p.project.metadata]))
    # TODO: only render allowlist if allowlist is not empty
    if p.project.cve_allowlist:
        tables.append(cveallowlist_table([p.project.cve_allowlist]))
    return Panel(Group(*tables), title=p.location, expand=True)
