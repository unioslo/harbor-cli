from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import UserGroupSearchItem
from rich.table import Table

from ...logs import logger
from ...models import UserGroupType
from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ._utils import get_table


def usergroupsearchitem_table(
    usergroups: Sequence[UserGroupSearchItem], **kwargs: Any
) -> Table:
    """Display one or more user group search items in a table."""
    table = get_table(
        "User Group Search Results",
        columns=[
            "ID",
            "Group Name",
            "Group Type",
        ],
    )
    for usergroup in usergroups:
        try:
            group_type = UserGroupType.from_int(usergroup.group_type).name  # type: ignore
        except ValueError as e:
            logger.warning(f"{e}")  # the exc message should be enough
            group_type = str(usergroup.group_type)
        table.add_row(
            int_str(usergroup.id),
            str_str(usergroup.group_name),
            str_str(group_type),
        )

    return table
