from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import Repository
from rich.table import Table

from ..formatting.dates import datetime_str
from ._utils import get_table


def repository_table(r: Sequence[Repository], **kwargs: Any) -> Table:
    """Display one or more repositories in a table."""
    table = get_table(
        "Repository",
        r,
        columns=[
            "Project",
            "Name",
            "Artifacts",
            "Created",
            "Updated",
        ],
    )
    for repo in r:
        table.add_row(
            repo.project_name,
            repo.name,
            str(repo.artifact_count),
            datetime_str(repo.creation_time),
            datetime_str(repo.update_time),
        )
    return table
