from __future__ import annotations

import typer

from ...app import app
from ...output.render import render_result
from ...state import get_state


state = get_state()


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="The search query."),
) -> None:
    """Search for projects and repositories.

    Provides the same functionality as the search bar in the header of Web UI.
    """
    results = state.run(state.client.search(query), "Searching...")
    render_result(results, ctx)
