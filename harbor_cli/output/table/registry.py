from __future__ import annotations

from typing import Sequence

from harborapi.models.models import RegistryProviderInfo
from harborapi.models.models import RegistryProviders
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ..formatting.builtin import str_str
from ._utils import get_panel
from ._utils import get_table


def registryproviders_panel(
    providers: Sequence[RegistryProviders],
) -> Panel:
    """Renders a list of RegistryProvider objects as individual tables in a panel."""
    if len(providers) > 1:
        logger.warning("Can only display one list of registry providers at a time")
    tables = []
    for name, provider in providers[0].providers.items():
        tables.append(_registryproviderinfo_table(name, provider))
    return get_panel(tables, title="Registry Providers", expand=True)


def _registryproviderinfo_table(name: str, provider: RegistryProviderInfo) -> Table:
    table = get_table(
        title=name,
        columns=[
            "Endpoint",
            "URL",
        ],
        pluralize=False,
    )

    if provider.endpoint_pattern and provider.endpoint_pattern.endpoints:
        for endpoint in provider.endpoint_pattern.endpoints:
            table.add_row(
                str_str(endpoint.key),
                str_str(endpoint.value),
            )
    return table
