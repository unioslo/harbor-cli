from __future__ import annotations

from typing import Sequence

from harborapi.models.models import UserResp
from rich.table import Table

from ._utils import get_table


def userresp_table(users: Sequence[UserResp]) -> Table:
    """Display one or more repositories in a table."""
    table = get_table("User", users)
    table.add_column("ID")
    table.add_column("Username")
    table.add_column("Full Name")

    # One volume per row
    for user in users:
        table.add_row(
            str(user.user_id),
            str(user.username),
            str(user.realname),
        )
    return table
