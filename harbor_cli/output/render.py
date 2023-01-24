from __future__ import annotations

from typing import Sequence
from typing import TypeVar

import typer
from harborapi.models.base import BaseModel as HarborBaseModel
from pydantic import BaseModel

from ..exceptions import OverwriteError
from ..logs import logger
from ..state import state
from .console import console
from .format import OutputFormat
from .schema import Schema
from .table import BuiltinTypeException
from .table import EmptySequenceError
from .table import get_renderable

T = TypeVar("T")

# TODO: add ResultType = T | list[T] to types.py


def render_result(result: T, ctx: typer.Context | None = None) -> None:
    """Render the result of a command."""
    fmt = state.config.output.format
    if fmt == OutputFormat.TABLE:
        render_table(result, ctx)
    elif fmt == OutputFormat.JSON:
        render_json(result, ctx)
    elif fmt == OutputFormat.JSONSCHEMA:
        render_jsonschema(result, ctx)
    else:
        raise ValueError(f"Unknown output format {fmt!r}.")


def render_table(result: T | Sequence[T], ctx: typer.Context | None = None) -> None:
    """Render the result of a command as a table."""
    # TODO: handle "primitives" like strings and numbers

    # Try to render compact table if enabled
    compact = state.config.output.table.compact
    if compact:
        try:
            render_table_compact(result)
        except NotImplementedError as e:
            logger.debug(f"Unable to render compact table: {e}")
        except (EmptySequenceError, BuiltinTypeException):
            pass  # can't render these types
        else:
            return

    # If we got to this point, we have not printed a compact table.
    # Use built-in table rendering from harborapi.
    render_table_full(result)


def render_table_compact(result: T | Sequence[T]) -> None:
    """Render the result of a command as a compact table."""
    renderable = get_renderable(result)
    console.print(renderable)


def render_table_full(result: T | Sequence[T]) -> None:
    show_description = state.config.output.table.description
    max_depth = state.config.output.table.max_depth

    def print_item(item: T) -> None:
        """Prints a harbor base model as a table (optionally with description),
        if it is a harborapi BaseModel, otherwise just prints the item."""
        if isinstance(item, HarborBaseModel):
            console.print(
                item.as_panel(with_description=show_description, max_depth=max_depth)
            )
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
    indent = state.config.output.JSON.indent
    # sort_keys = state.config.output.JSON.sort_keys

    # To make the JSON serialization more compatible with Pydantic
    # models and data types, we wrap the data in a Pydantic model
    # with a single field named __root__, which renders the data
    # as the root value of the JSON object:
    # Output(__root__={"foo": "bar"}).json() -> '{"foo": "bar"}'
    class Output(BaseModel):
        __root__: T | list[T]

    o = Output(__root__=result)
    o_json = o.json(indent=indent)
    if p:
        if p.exists() and no_overwrite:
            raise OverwriteError(f"File {p.resolve()} exists.")
        with open(p, "w") as f:
            f.write(o_json)
            logger.info(f"Output written to {p.resolve()}")
    # Print to stdout if no output file is specified or if the
    # --with-stdout flag is set.
    if not p or with_stdout:
        # We have to specify indent again here, because
        # rich.console.Console.print_json() ignores the indent of
        # the string passed to it.
        console.print_json(o_json, indent=indent)


def render_jsonschema(
    result: T | Sequence[T], ctx: typer.Context | None = None
) -> None:
    """Render the result of a command as JSON with metadata."""
    p = state.options.output_file
    with_stdout = state.options.with_stdout
    no_overwrite = state.options.no_overwrite
    indent = state.config.output.JSON.indent
    # sort_keys = state.config.output.JSON.sort_keys

    # TODO: add switch to print to file and stdout at the same time
    schema = Schema(data=result)  # type: Schema[T | list[T]]
    schema_json = schema.json(indent=indent)
    if p:
        if p.exists() and no_overwrite:
            raise FileExistsError(f"File {p} exists.")
        with open(p, "w") as f:
            f.write(schema_json)
    if not p or with_stdout:
        console.print_json(schema_json, indent=indent)
