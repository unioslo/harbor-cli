from __future__ import annotations

from typing import Sequence
from typing import TypeVar

import typer
from pydantic import BaseModel

from ..context import get_output_file
from ..context import get_output_format
from .console import console
from .format import OutputFormat
from .schema import Schema


T = TypeVar("T", BaseModel, str)

# TODO: add ResultType = T | list[T] to types.py


def render_result(result: T | Sequence[T], ctx: typer.Context) -> None:
    """Render the result of a command."""
    fmt = get_output_format(ctx)
    if fmt == OutputFormat.TABLE:
        render_table(result, ctx)
    elif fmt == OutputFormat.JSON:
        render_json(result, ctx)
    else:
        raise ValueError(f"Unknown output format {fmt!r}.")


def render_table(result: T | Sequence[T], ctx: typer.Context) -> None:
    """Render the result of a command as a table."""
    if isinstance(result, list):
        for item in result:
            console.print(item)
    else:
        console.print(result)


def render_json(result: T | Sequence[T], ctx: typer.Context) -> None:
    """Render the result of a command as JSON."""
    p = get_output_file(ctx)

    # TODO: add switch to print to file and stdout at the same time
    schema = Schema(data=result)  # type: Schema[T | list[T]]
    if p:
        with open(p, "w") as f:
            f.write(schema.json())
    else:
        # If we are only rendering to stdout, we don't need to include
        # the schema metadata in the output.
        # To make the JSON serialization more compatible with Pydantic
        # models and data types, we wrap the data in a Pydantic model
        # with a single field named __root__, which renders the data
        # as the root value of the JSON object:
        # Output(__root__={"foo": "bar"}).json() -> '{"foo": "bar"}'

        class Output(BaseModel):
            __root__: T | list[T]

        res_json = Output(__root__=schema.data).json()
        console.print_json(res_json)
