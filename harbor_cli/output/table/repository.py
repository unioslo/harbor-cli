from __future__ import annotations

from typing import Sequence

from harborapi.models.models import Repository
from rich.table import Table

from ..formatting.dates import datetime_str


def repository_table(r: Repository | Sequence[Repository]) -> Table:
    """Display one or more repositories in a table."""
    if isinstance(r, Repository):
        r = [r]
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Project")
    table.add_column("Name")
    table.add_column("Artifacts")
    table.add_column("Created")
    table.add_column("Updated")
    for repo in r:
        table.add_row(
            repo.project_name,
            repo.name,
            str(repo.artifact_count),
            datetime_str(repo.creation_time),
            datetime_str(repo.update_time),
        )
    return table
