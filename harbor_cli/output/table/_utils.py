from __future__ import annotations

from typing import Any
from typing import Optional
from typing import Sequence
from typing import TYPE_CHECKING

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from ...state import get_state
from ..formatting.builtin import plural_str

if TYPE_CHECKING:
    from typing_extensions import Unpack
    from rich.console import OverflowMethod
    from rich.console import RenderableType, JustifyMethod
    from rich.align import VerticalAlignMethod
    from rich.style import StyleType
    from harbor_cli.types import RichTableKwargs


state = get_state()


def get_table(
    title: str | None = None,
    data: Sequence[Any] | None = None,  # not a rich Table kwarg
    pluralize: bool = True,  # not a rich Table kwarg
    columns: list[str] | None = None,  # not a rich Table kwarg
    **kwargs: Unpack[RichTableKwargs],
) -> Table:
    """Get a table with our defaults."""
    # NOTE: This is a bug waiting to manifest itself.
    # Maybe we should raise exception if we pass title and pluralize
    # but not data.
    if title and pluralize and data is not None:
        title = plural_str(title, data)

    # Set kwargs defaults (so we don't accidentally pass them twice)
    styleconf = state.config.output.table.style
    style_kwargs = styleconf.as_rich_kwargs()
    for k, v in style_kwargs.items():
        kwargs.setdefault(k, v)  # type: ignore [misc] # accessing key with variable instead of literal
    table = Table(title=title, **kwargs)
    if columns is not None:
        for column in columns:
            add_column(table, column)
    return table


def add_column(
    table: Table,
    header: "RenderableType" = "",
    footer: "RenderableType" = "",
    *,
    header_style: Optional[StyleType] = None,
    footer_style: Optional[StyleType] = None,
    style: Optional[StyleType] = None,
    justify: "JustifyMethod" = "left",
    vertical: "VerticalAlignMethod" = "top",
    overflow: "OverflowMethod" = "fold",
    width: Optional[int] = None,
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    ratio: Optional[int] = None,
    no_wrap: bool = False,
) -> None:
    """Add a column to a table with our default style."""
    table.add_column(
        header,
        footer,
        header_style=header_style,
        footer_style=footer_style,
        style=style,
        justify=justify,
        vertical=vertical,
        overflow=overflow,
        width=width,
        min_width=min_width,
        max_width=max_width,
        ratio=ratio,
        no_wrap=no_wrap,
    )


def get_panel(renderables: Sequence[RenderableType], title: str | None = None) -> Panel:
    """Get a panel from a sequence of renderables."""
    expand = state.config.output.table.style.expand
    return Panel(Group(*renderables), title=title, expand=expand)
