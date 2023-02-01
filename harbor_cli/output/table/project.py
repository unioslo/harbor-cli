from __future__ import annotations

from typing import Sequence

from harborapi.models.models import Project
from rich.table import Table

from ..formatting.builtin import plural_str
from ..formatting.dates import datetime_str


def project_table(p: Sequence[Project]) -> Table:
    """Display one or more repositories in a table."""
    table = Table(
        title=plural_str("Project", p), show_header=True, header_style="bold magenta"
    )
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Public")
    table.add_column("Repositories")
    table.add_column("Creation Time")
    for project in p:
        table.add_row(
            str(project.name),
            str(project.project_id),
            str(project.metadata.public) if project.metadata else "Unknown",
            str(project.repo_count),
            datetime_str(project.creation_time),
        )
    return table
