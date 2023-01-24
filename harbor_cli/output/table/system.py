from __future__ import annotations

from typing import Sequence

from harborapi.models.models import Storage
from harborapi.models.models import SystemInfo
from rich.table import Table

from ...logs import logger
from ..formatting.bytes import bytes_to_str


def systeminfo_table(systeminfo: Sequence[SystemInfo]) -> Table:
    """Display one or more repositories in a table."""
    if len(systeminfo) > 1:
        # should never happen
        logger.warning("Can only display one system info at a time.")
    info = systeminfo[0]

    table = Table(show_header=True, header_style="bold magenta")
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
            bytes_to_str(total),
            bytes_to_str(free),
            bytes_to_str(used),
        )
    return table
