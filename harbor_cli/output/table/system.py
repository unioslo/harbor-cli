from __future__ import annotations

from harborapi.models.models import Storage
from harborapi.models.models import SystemInfo
from rich.table import Table

from ..formatting.bytes import bytes_to_str


def systeminfo_table(model: SystemInfo) -> Table:
    """Display one or more repositories in a table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Total Capacity")
    table.add_column("Free Space")
    table.add_column("Used Space")  # calculated

    # Add empty row if no storage
    if not model.storage:
        model.storage = [Storage(total=0, free=0)]

    # One volume per row
    for storage in model.storage:
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
