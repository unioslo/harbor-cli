from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import RegistryProviderInfo
from harborapi.models.models import RegistryProviders
from rich.table import Table

from ...logs import logger
from ..formatting.builtin import str_str
from ._utils import get_table


def registryproviders_table(
    providers: Sequence[RegistryProviders], **kwargs: Any
) -> Table:
    """Renders a list of RegistryProvider objects as individual tables in a panel."""
    if len(providers) > 1:
        logger.warning("Can only display one list of registry providers at a time")
    prov = providers[0]
    table = get_table("Registry Providers", columns=["Name", "Info"], show_lines=True)
    for name, provider in prov.providers.items():
        table.add_row(name, _registryproviderinfo_table(provider))
    return table


def _registryproviderinfo_table(provider: RegistryProviderInfo, **kwargs: Any) -> Table:
    table = get_table(
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
