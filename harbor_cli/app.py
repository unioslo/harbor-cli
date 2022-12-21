from __future__ import annotations

import typer

app = typer.Typer(
    help="Harbor CLI",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
    # rich_markup_mode needs to be set here!
    # Sub-commands will inherit this setting,
    # but it has no effect if only set in sub-commands
    rich_markup_mode="rich",
)
