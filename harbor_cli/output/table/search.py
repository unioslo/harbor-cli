from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import Search
from harborapi.models.models import SearchRepository
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ..formatting.builtin import bool_str
from ..formatting.builtin import int_str
from ._utils import get_table
from .project import project_table


def search_panel(search: Sequence[Search], **kwargs: Any) -> Panel:
    """Display one or more repositories in a table."""
    if len(search) != 1:
        logger.warning("Can only display one search result at a time.")
    s = search[0]  # guaranteed to be at least one result

    tables = []
    # Re-use the project table function
    if s.project:
        tables.append(project_table(s.project))

    if s.repository:
        tables.append(searchrepo_table(s.repository))

    return Panel(Group(*tables), title=f"Search Results", expand=True)


def searchrepo_table(repos: Sequence[SearchRepository], **kwargs: Any) -> Table:
    table = get_table(
        "Repository",
        repos,
        columns=[
            "Project",
            "Name",
            "Artifacts",
            "Public",
        ],
    )
    for repo in repos:
        table.add_row(
            str(repo.project_name),
            str(repo.repository_name),
            int_str(repo.artifact_count),
            bool_str(repo.project_public),
        )
    return table
