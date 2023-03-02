from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import UserResp
from harborapi.models.models import UserSearchRespItem
from rich.table import Table

from ._utils import get_table


def userresp_table(users: Sequence[UserResp], **kwargs: Any) -> Table:
    """Display one or more users in a table."""
    table = get_table(
        "User",
        users,
        columns=["ID", "Username", "Full Name"],
    )
    for user in users:
        table.add_row(
            str(user.user_id),
            str(user.username),
            str(user.realname),
        )
    return table


def usersearchrespitem_table(
    users: Sequence[UserSearchRespItem], **kwargs: Any
) -> Table:
    """Display one or more users found in a user search."""
    table = get_table("Results", columns=["ID", "Username"])

    for user in users:
        table.add_row(
            str(user.user_id),
            str(user.username),
        )
    return table
