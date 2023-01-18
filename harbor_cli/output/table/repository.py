from __future__ import annotations

from harborapi.models.models import Repository
from rich.table import Table


def repository_table(r: Repository | list[Repository]) -> Table:
    """Display one or more repositories in a table."""
    if isinstance(r, Repository):
        r = [r]
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Project")
    table.add_column("Name")
    table.add_column("Artifacts")
    table.add_column("Created")
    for repo in r:
        table.add_row(
            repo.project_name,
            repo.name,
            str(repo.artifact_count),
            str(repo.creation_time),
        )
    return table
