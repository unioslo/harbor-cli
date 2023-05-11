from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from click_repl import repl as start_repl
from prompt_toolkit.history import FileHistory

from ...app import app
from ...config import DEFAULT_HISTORY_FILE
from ...config import env_var
from ...option import Option
from ...state import get_state
from ...style import render_cli_value

state = get_state()


@app.command()
def repl(
    ctx: typer.Context,  # REPL options
    repl_history: Optional[bool] = Option(
        None,
        "--repl-history/--no-repl-history",
        help="Enable REPL history.",
        envvar=env_var("repl_history"),
        config_override="repl.history",
    ),
    repl_history_file: Optional[Path] = Option(
        None,
        "--repl-history-file",
        help=f"Custom location of REPL history file (default: {render_cli_value(str(DEFAULT_HISTORY_FILE))}).",
        envvar=env_var("repl_history_file"),
        config_override="repl.history_file",
    ),
) -> None:
    """Start an interactive REPL."""
    # Overrides for REPL config options
    # NOTE: we specify them here instead of the main callback, because it
    # makes no sense to expose these options if we're already in REPL mode.
    if repl_history:
        state.config.repl.history = repl_history
    if repl_history_file:
        state.config.repl.history_file = repl_history_file

    state.repl = True
    prompt_kwargs = {}
    if state.config.repl.history:
        prompt_kwargs["history"] = FileHistory(str(state.config.repl.history_file))
    start_repl(ctx, prompt_kwargs=prompt_kwargs)
