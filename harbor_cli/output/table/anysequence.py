from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.base import BaseModel
from rich.table import Table


class AnySequence(BaseModel):
    """Pydantic model that can contain a sequence of any type.

    Used to render arbitrary sequences of objects as a table where
    each row consists of 1 column showing 1 value."""

    title: str = "Values"
    values: Sequence[Any] = []


def anysequence_table(s: Sequence[AnySequence]) -> Table:
    """Renders an AnySequence as a table."""
    table = Table(show_header=True, header_style="bold magenta")
    try:
        title = s[0].title
    except IndexError:
        title = "Values"
    table.add_column(title)
    for idx, seq in enumerate(s):
        for item in seq.values:
            table.add_row(
                item,
            )
        if idx < len(s) - 1:  # add a section between each sequence
            table.add_section()  # type: ignore # it definitely has this method?!
    return table
