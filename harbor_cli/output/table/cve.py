from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import CVEAllowlist
from rich.table import Table

from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.dates import datetime_str
from ._utils import get_table


def cveallowlist_table(c: Sequence[CVEAllowlist], **kwargs: Any) -> Table:
    table = get_table(
        "CVE Allowlist",
        c,
        columns=[
            "ID",
            "Items",
            "Expires",
            "Created",
            "Updated",
        ],
    )
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
