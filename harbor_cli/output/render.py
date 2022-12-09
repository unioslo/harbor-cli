from __future__ import annotations

import json
from typing import TypeVar

import typer
from pydantic import BaseModel

from ..context import get_output_file
from ..context import get_output_format
from .console import console
from .format import OutputFormat


T = TypeVar("T")


def render_result(result: T | list[T], ctx: typer.Context) -> None:
    """Render the result of a command."""
    fmt = get_output_format(ctx)
    if fmt == OutputFormat.TABLE:
        render_table(result, ctx)
    elif fmt == OutputFormat.JSON:
        render_json(result, ctx)
    else:
        raise ValueError(f"Unknown output format {fmt!r}.")


def render_table(result: T | list[T], ctx: typer.Context) -> None:
    """Render the result of a command as a table."""
    if isinstance(result, list):
        for item in result:
            console.print(item)
    else:
        console.print(result)


def render_json(result: T | list[T], ctx: typer.Context) -> None:
    """Render the result of a command as JSON."""
    # If we have a lits of results, it's likely a list of BaseModel objects
    if isinstance(result, list):  # TODO: use Sequence instead?
        if all(isinstance(item, BaseModel) for item in result):

            class Container(BaseModel):
                __root__: list[BaseModel]

            c = Container(__root__=result)
            res_json = c.json()
        else:
            res_json = json.dumps(result)
    else:
        # Prefer to use Pydantic models' json() method if available
        if isinstance(result, BaseModel):
            res_json = result.json()
        else:
            res_json = json.dumps(result)

    p = get_output_file(ctx)

    # TODO: add switch to print to file and stdout at the same time
    if p:
        with open(p, "w") as f:
            f.write(res_json)
    else:
        console.print_json(res_json)
