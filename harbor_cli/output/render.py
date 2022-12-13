from __future__ import annotations

from typing import Sequence
from typing import TypeVar

import typer
from pydantic import BaseModel

from ..context import get_no_overwrite
from ..context import get_output_file
from ..context import get_output_format
from ..context import get_with_stdout
from ..exceptions import OverwriteError
from .console import console
from .format import OutputFormat
from .schema import Schema


T = TypeVar("T")

# TODO: add ResultType = T | list[T] to types.py


def render_result(result: T, ctx: typer.Context) -> None:
    """Render the result of a command."""
    fmt = get_output_format(ctx)
    if fmt == OutputFormat.TABLE:
        render_table(result, ctx)
    elif fmt == OutputFormat.JSON:
        render_json(result, ctx)
    elif fmt == OutputFormat.JSONSCHEMA:
        render_jsonschema(result, ctx)
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
    with_stdout = get_with_stdout(ctx)
    no_overwrite = get_no_overwrite(ctx)

    # To make the JSON serialization more compatible with Pydantic
    # models and data types, we wrap the data in a Pydantic model
    # with a single field named __root__, which renders the data
    # as the root value of the JSON object:
    # Output(__root__={"foo": "bar"}).json() -> '{"foo": "bar"}'
    class Output(BaseModel):
        __root__: T | list[T]

    o = Output(__root__=result)
    o_json = o.json(indent=4)
    if p:
        if p.exists() and no_overwrite:
            raise OverwriteError(f"File {p.resolve()} exists.")
        with open(p, "w") as f:
            f.write(o_json)
    # Print to stdout if no output file is specified or if the
    # --with-stdout flag is set.
    if not p or with_stdout:
        console.print_json(o_json)


def render_jsonschema(result: T | Sequence[T], ctx: typer.Context) -> None:
    """Render the result of a command as JSON with metadata."""
    p = get_output_file(ctx)
    with_stdout = get_with_stdout(ctx)
    no_overwrite = get_no_overwrite(ctx)

    # TODO: add switch to print to file and stdout at the same time
    schema = Schema(data=result)  # type: Schema[T | list[T]]
    schema_json = schema.json(indent=4)
    if p:
        if p.exists() and no_overwrite:
            raise FileExistsError(f"File {p} exists.")
        with open(p, "w") as f:
            f.write(schema_json)
    if not p or with_stdout:
        console.print_json(schema_json)
