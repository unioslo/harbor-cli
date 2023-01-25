from __future__ import annotations

from typing import Sequence

from rich.table import Table

from ...models import CommandSummary
from ..formatting.builtin import int_str


def commandsummary_table(c: Sequence[CommandSummary]) -> Table:
    """Display summary of commands in a table."""
    table = Table(title="Results", show_header=True, header_style="bold magenta")
    table.add_column("Command")
    table.add_column("Description")
    table.add_column("Match")
    for cmd in c:
        table.add_row(
            cmd.name,
            cmd.help,
            int_str(cmd.score),
        )
    return table
