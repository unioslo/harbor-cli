from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.base import BaseModel
from rich.table import Table

from ._utils import get_table


class AnySequence(BaseModel):
    """Pydantic model that can contain a sequence of any type.

    Used to render arbitrary sequences of objects as a table where
    each row consists of 1 column showing 1 value."""

    title: str = "Values"
    values: Sequence[Any] = []


def anysequence_table(s: Sequence[AnySequence], **kwargs: Any) -> Table:
    """Renders an AnySequence as a table."""
    # No title here I think...?
    try:
        title = s[0].title
    except IndexError:
        title = "Values"
    table = get_table(columns=[title])
    for idx, seq in enumerate(s):
        for item in seq.values:
            table.add_row(
                item,
            )
        if idx < len(s) - 1:  # add a section between each sequence
            table.add_section()
    return table
