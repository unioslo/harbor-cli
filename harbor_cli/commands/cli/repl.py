from __future__ import annotations

import typer
from click_repl import repl as start_repl
from prompt_toolkit.history import FileHistory

from ...app import app
from ...state import state


@app.command()
def repl(ctx: typer.Context) -> None:
    """Start an interactive REPL."""
    state.repl = True
    prompt_kwargs = {}
    if state.config.general.history:
        prompt_kwargs["history"] = FileHistory(str(state.config.general.history_file))
    start_repl(ctx, prompt_kwargs=prompt_kwargs)
