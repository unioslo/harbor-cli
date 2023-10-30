from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import Registry
from harborapi.models.models import RegistryCredential
from harborapi.models.models import RegistryProviders
from rich.table import Table

from ...logs import logger
from ..formatting.builtin import bool_str
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.constants import NONE_STR
from ..formatting.dates import datetime_str
from ._utils import get_table


def registryproviders_table(
    providers: Sequence[RegistryProviders], **kwargs: Any
) -> Table:
    """Renders a list of RegistryProvider objects as individual tables in a panel."""
    if len(providers) != 1:
        logger.warning("Can only display one list of registry providers at a time")
    prov = providers[0]
    table = get_table(
        "Registry Providers", columns=["Name", "Endpoint", "URL"], show_lines=False
    )
    for name, provider in prov.root.items():
        if not provider.endpoint_pattern or not provider.endpoint_pattern.endpoints:
            continue
        for idx, endpoint in enumerate(provider.endpoint_pattern.endpoints):
            name = name if idx == 0 else ""
            table.add_row(
                str_str(name),
                str_str(endpoint.key),
                str_str(endpoint.value),
            )
        else:
            table.add_section()
    return table


def registrycredential_table(credential: RegistryCredential, **kwargs: Any) -> Table:
    """Renders a list of RegistryProvider objects as individual tables in a panel."""
    table = get_table(
        "Registry Credential",
        columns=[
            "Type",
            "Access Key",
            "Access Secret",
        ],
    )
    table.add_row(
        str_str(credential.type),
        str_str(credential.access_key),
        str_str(credential.access_secret),
    )
    return table


def registry_table(registries: Sequence[Registry], **kwargs: Any) -> Table:
    """Renders a list of RegistryProvider objects as individual tables in a panel."""
    table = get_table(
        "Registries",
        columns=[
            "ID",
            "URL",
            "Name",
            "Credential",
            "Type",
            "insecure",
            "Description",
            "Status",
            "Creation Time",
            "Update Time",
        ],
    )
    for registry in registries:
        if registry.credential:
            credential = registrycredential_table(registry.credential)
        else:
            credential = NONE_STR  # type: ignore
        table.add_row(
            int_str(registry.id),
            str_str(registry.url),
            str_str(registry.name),
            credential,
            str_str(registry.type),
            bool_str(registry.insecure),
            str_str(registry.description),
            str_str(registry.status),
            datetime_str(registry.creation_time),
            datetime_str(registry.update_time),
        )
    return table
