from __future__ import annotations

import time
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Iterable
from typing import List

import typer
from pydantic import BaseModel
from rich.table import Table

from ...cache import Cache
from ...output.console import console
from ...output.console import info
from ...output.render import render_result
from ...output.table._utils import get_table
from ...state import get_state

state = get_state()

# Create a command group
app = typer.Typer(
    name="cache",
    help="Manage the CLI REPL cache.",
    no_args_is_help=True,
)


# TODO: refactor. move this function so it can be re-used by other commands
def fmt_timedelta(td: timedelta) -> str:
    """Format a timedelta object as a string."""
    s = ""
    if td.days:
        s += f"{td.days}d "
    # Show hours if we have more than 60 minutes
    if td.seconds >= 3600:
        s += f"{td.seconds // 3600}h "
    # Show minutes if we have more than 60 seconds
    if td.seconds % 3600 >= 60:
        s += f"{(td.seconds % 3600) // 60}m "
    # Show seconds if we have more than 0 seconds
    if td.seconds % 60:
        s += f"{td.seconds % 60}s"
    return s.strip()


class CachedItemInfo(BaseModel):
    key: str
    items: int
    expiry: float

    @property
    def expiry_str(self) -> str:
        t = time.time()
        if self.expiry < t:
            return "expired"
        exp = datetime.fromtimestamp(self.expiry) - datetime.fromtimestamp(t)
        return fmt_timedelta(exp)


class CacheInfo(BaseModel):
    commands: List[CachedItemInfo]

    @property
    def empty(self) -> bool:
        return not self.commands or not any(c.items for c in self.commands)

    def __rich_console__(self, console: Any, options: Any) -> Iterable[Table]:
        table = get_table("Cache Info", columns=["Command", "# Items", "Expires"])
        for command in self.commands:
            table.add_row(command.key, str(command.items), command.expiry_str)
        if table.rows:
            yield table

    @classmethod
    def from_cache(cls, cache: Cache) -> CacheInfo:
        commands = []
        for k, v in cache.items():
            # Count number of cached items for this key
            try:
                # The cached item might be a sequence, but we count
                # strings as 1 item, so we can't run len() on them.
                if isinstance(v.value, str):
                    n_items = 1
                else:
                    n_items = len(v.value)
            except TypeError:
                n_items = 1 if v.value else 0
            commands.append(CachedItemInfo(key=k, items=n_items, expiry=v.expiry))
        return cls(commands=commands)


@app.command("info")
def cache_info(ctx: typer.Context) -> None:
    """Show information about the internal CLI cache."""
    cache_info = CacheInfo.from_cache(state.cache)
    # NOTE: why not just cache.empty?
    if cache_info.empty:
        info("Cache is empty.")
    render_result(cache_info, ctx)


@app.command("clear")
def cache_clear(ctx: typer.Context) -> None:
    """Clear the CLI's internal cache."""
    state.cache.clear()
    console.print("Cache cleared.")
