from __future__ import annotations

from typing import Sequence
from typing import TypeVar

import typer
from harborapi.models.base import BaseModel as HarborBaseModel
from pydantic import BaseModel

from ..exceptions import OverwriteError
from ..state import state
from .console import console
from .format import OutputFormat
from .schema import Schema

T = TypeVar("T")

# TODO: add ResultType = T | list[T] to types.py


def render_result(result: T, ctx: typer.Context) -> None:
    """Render the result of a command."""
    fmt = state.options.output_format
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
    show_description = state.options.show_description

    def print_item(item: T) -> None:
        """Prints a harbor base model as a table (optionally with description),
        if it is a harborapi BaseModel, otherwise just prints the item."""
        if isinstance(item, HarborBaseModel):
            console.print(*(item.as_table(with_description=show_description)))
        else:
            console.print(item)

    if isinstance(result, Sequence):
        for item in result:
            print_item(item)
    else:
        print_item(result)


def render_json(result: T | Sequence[T], ctx: typer.Context | None = None) -> None:
    """Render the result of a command as JSON."""
    p = state.options.output_file
    with_stdout = state.options.with_stdout
    no_overwrite = state.options.no_overwrite

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


def render_jsonschema(
    result: T | Sequence[T], ctx: typer.Context | None = None
) -> None:
    """Render the result of a command as JSON with metadata."""
    p = state.options.output_file
    with_stdout = state.options.with_stdout
    no_overwrite = state.options.no_overwrite

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
