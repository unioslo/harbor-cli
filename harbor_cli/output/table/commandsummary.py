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

    # If we got these commands from a search, we can show a score
    has_score = any(cmd.score for cmd in c)
    if has_score:
        table.add_column("Match", justify="right")

    for cmd in c:
        row = [cmd.name, cmd.help]
        if has_score:
            row.append(int_str(cmd.score))
        table.add_row(*row)
    return table
