from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import AuthproxySetting
from harborapi.models.models import GeneralInfo
from harborapi.models.models import OverallHealthStatus
from harborapi.models.models import Statistic
from harborapi.models.models import Storage
from harborapi.models.models import SystemInfo
from rich import box
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ...style.color import HealthColor
from ..formatting.builtin import bool_str
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.bytes import bytesize_str
from ._utils import get_panel
from ._utils import get_table


# The ironic thing is that this is not actually system info, but storage info.
# GeneralInfo is the model used for general system info.
def systeminfo_table(systeminfo: Sequence[SystemInfo], **kwargs: Any) -> Table:
    """Display system info in a table."""
    if len(systeminfo) != 1:
        # should never happen
        logger.warning("Can only display one system info at a time.")
    info = systeminfo[0]

    table = get_table(
        "System Info",
        pluralize=False,
        columns=["Total Capacity", "Free Space", "Used Space"],
    )

    # Add empty row if no storage
    if not info.storage:
        info.storage = [Storage(total=0, free=0)]

    # One volume per row
    for storage in info.storage:
        # Values are Optional[int]!
        # We could end up with negative used value if total is missing
        # but free is present. Not our problem.
        total = storage.total or 0
        free = storage.free or 0
        used = total - free
        table.add_row(
            bytesize_str(total),
            bytesize_str(free),
            bytesize_str(used),
        )
    return table


def overallhealthstatus_panel(health: OverallHealthStatus, **kwargs) -> Panel:
    # Show overall health status at the top
    status_color = HealthColor.from_health(health.status)
    status = f"[{status_color}]{health.status}[/]"
    status_table = Table.grid()
    status_table.add_row("Status: ", status)

    # Individual component statuses in a table
    table = get_table(
        "Components",
        columns=[
            "Component",
            "Status",
            "Error",
        ],
    )
    health.components = health.components or []
    for component in health.components:
        status_style = "green" if component.status == "healthy" else "red"
        table.add_row(
            str_str(component.name),
            f"[{status_style}]{str_str(component.status)}[/]",
            str_str(component.error),
        )

    return get_panel([status_table, table], title="System Health")


def generalinfo_panel(info: GeneralInfo, **kwargs) -> Panel:
    """Displays panel for `system info` command."""
    # Split up system info into multiple tables (categories)
    tables = []

    # General
    general_table = get_table(
        "General",
        columns=[
            "Registry URL",
            "External URL",
            "Harbor Version",
            "Registry Storage Provider",
            "Read Only",
        ],
    )
    general_table.add_row(
        str_str(info.registry_url),
        str_str(info.external_url),
        str_str(info.harbor_version),
        str_str(info.registry_storage_provider_name),
        bool_str(info.read_only),
    )
    tables.append(general_table)

    # Authentication
    auth_table = get_table(
        "Authentication",
        columns=[
            "Mode",
            "Primary Auth Mode",
            "Project Creation Restriction",
            "Self Registration",
            "Has CA Root",
        ],
    )
    auth_table.add_row(
        str_str(info.auth_mode),
        bool_str(info.primary_auth_mode),
        str_str(info.project_creation_restriction),
        bool_str(info.self_registration),
        bool_str(info.has_ca_root),
    )
    tables.append(auth_table)

    # Add auth proxy settings table if present
    if info.authproxy_settings:
        tables.append(authproxysetting_table(info.authproxy_settings), **kwargs)

    # Model is called "GeneralInfo", but it's for system info
    return get_panel(tables, title="System Info")


def authproxysetting_table(auth: AuthproxySetting, **kwargs) -> Table:
    table = get_table(
        "Auth Proxy Settings",
        columns=[
            "Endpoint",
            "Token Review Endpoint",
            "Skip Search",
            "Verify Cert",
            "Server Certificate",
        ],
    )
    table.add_row(
        str_str(auth.endpoint),
        str_str(
            auth.tokenreivew_endpoint
        ),  # TODO: fix spelling when harborapi is fixed
        bool_str(auth.skip_search),
        bool_str(auth.verify_cert),
        str_str(auth.server_certificate),
    )
    return table


def statistic_table(stats: Statistic, **kwargs) -> Table:
    """Displays table for `system statistics` command."""
    table = get_table(
        "Statistics",
        columns=[
            "Projects",
            "Repos",
            "Storage",
        ],
    )

    # Wrap this field in a table for consistent presentation
    storage_table = get_table(columns=["Used"], box=box.SQUARE)
    storage_table.add_row(bytesize_str(stats.total_storage_consumption))

    table.add_row(
        _pubprivtotal_table(
            stats.public_project_count,
            stats.private_project_count,
            stats.total_project_count,
        ),
        _pubprivtotal_table(
            stats.public_repo_count, stats.private_repo_count, stats.total_repo_count
        ),
        storage_table,
    )
    return table


def _pubprivtotal_table(
    public: int | None, private: int | None, total: int | None, **kwargs
) -> Table:
    """Abstraction to display public/private/total counts in a table"""
    table = get_table(columns=["Public", "Private", "Total"], box=box.SQUARE)
    table.add_row(
        int_str(public),
        int_str(private),
        int_str(total),
    )
    return table
