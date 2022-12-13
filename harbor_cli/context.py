from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from .output.format import OutputFormat


def _get_ctx_params(ctx: typer.Context) -> dict[str, Any]:
    """Recursively gets all params from the context and its parent contexts.

    This way we can get the global options from the parent context, no
    matter how deeply nested the command is.

    Parameters
    ----------
    ctx : typer.Context
        The context to get the params from.

    Returns
    -------
    dict[str, Any]
        A dictionary of all params from the context and its parent contexts.
    """
    params = {}
    p = ctx.parent
    while p:
        params.update(p.params)
        p = p.parent
    return params


def get_output_format(ctx: typer.Context) -> OutputFormat:
    """Get the output format from the context."""
    params = _get_ctx_params(ctx)
    try:
        return OutputFormat(params["output_format"])  # type: ignore
    except (AttributeError, KeyError):
        return OutputFormat.TABLE


def get_output_file(ctx: typer.Context) -> Path | None:
    """Get the output path from the context."""
    params = _get_ctx_params(ctx)
    try:
        return params["output_file"]  # type: ignore
    except (AttributeError, KeyError):
        return None


def get_with_stdout(ctx: typer.Context) -> bool:
    """Get the with_stdout flag from the context."""
    params = _get_ctx_params(ctx)
    try:
        return bool(params["with_stdout"])  # type: ignore
    except (AttributeError, KeyError):
        return False
