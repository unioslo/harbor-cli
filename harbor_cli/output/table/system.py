from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import Storage
from harborapi.models.models import SystemInfo
from rich.table import Table

from ...logs import logger
from ..formatting.bytes import bytesize_str
from ._utils import get_table


# The ironic thing is that this is not actually system info, but storage info.
# GeneralInfo is the model used for general system info.
def systeminfo_table(systeminfo: Sequence[SystemInfo], **kwargs: Any) -> Table:
    """Display system info in a table."""
    if len(systeminfo) > 1:
        # should never happen
        logger.warning("Can only display one system info at a time.")
    info = systeminfo[0]

    table = get_table("System Info", pluralize=False)
    table.add_column("Total Capacity")
    table.add_column("Free Space")
    table.add_column("Used Space")  # calculated

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
