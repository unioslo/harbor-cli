from __future__ import annotations

from typing import Any
from typing import Sequence

from rich.console import Group
from rich.console import OverflowMethod
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table

from ...state import get_state
from ..formatting.builtin import plural_str


state = get_state()


def get_table(
    title: str | None = None,
    data: Sequence[Any] | None = None,
    pluralize: bool = True,
    columns: list[str] | None = None,
    overflow: OverflowMethod = "fold",
    **kwargs: Any,
) -> Table:
    """Get a table with a title."""
    # NOTE: This is a bug waiting to manifest itself.
    # Maybe we should raise exception if we pass title and pluralize
    # but not data.
    if title and pluralize and data is not None:
        title = plural_str(title, data)

    # Set kwargs defaults (so we don't accidentally pass them twice)
    styleconf = state.config.output.table.style
    style_kwargs = styleconf.as_rich_kwargs()
    for k, v in style_kwargs.items():
        kwargs.setdefault(k, v)

    table = Table(
        title=title,
        **kwargs,
    )
    if columns is not None:
        for column in columns:
            table.add_column(column, overflow=overflow)
    return table


def get_panel(renderables: Sequence[RenderableType], title: str | None = None) -> Panel:
    """Get a panel from a sequence of renderables."""
    expand = state.config.output.table.style.expand
    return Panel(Group(*renderables), title=title, expand=expand)
