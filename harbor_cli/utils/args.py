from __future__ import annotations

from typing import Any
from typing import List
from typing import Type
from typing import TypeVar

import typer
from pydantic import BaseModel

from ..output.console import exit_err

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)


def model_params_from_ctx(
    ctx: typer.Context, model: Type[BaseModel], filter_none: bool = True
) -> dict[str, Any]:
    """Get the model parameters from a Typer context.

    Given a command where the function parameter names match the
    model field names, this function will return a dictionary of only the
    parameters that are valid for the model.

    If `filter_none` is True, then parameters that are None will be filtered out.
    This is enabled by default, since most Harbor API model fields are optional,
    and we want to signal to Pydantic that these fields should be treated
    as "unset" rather than "set to None".

    Parameters
    ----------
    ctx : typer.Context
        The Typer context.
    filter_none : bool
        Whether to filter out None values, by default True

    Returns
    -------
    dict[str, Any]
        The model parameters.
    """
    return {
        key: value
        for key, value in ctx.params.items()
        if key in model.__fields__ and value is not None
    }


def create_updated_model(
    existing: BaseModel,
    new: Type[BaseModelType],
    ctx: typer.Context,
    extra: bool = False,
    empty_ok: bool = False,
) -> BaseModelType:
    """Given a BaseModel and a new model type, create a new model
    from the fields of the existing model combined with the arguments given
    to the command in the Typer context.

    Basically, when we call a PUT enpdoint, the API expects the full model definition,
    but we want to allow the user to only specify the fields they want to update.
    This function allows us to do that, by taking the existing model and updating
    it with the new values from the Typer context (which derives its parameters
    from the model used in send the PUT request.)

    Examples
    --------
    >>> from pydantic import BaseModel
    >>> class Foo(BaseModel):
    ...     a: Optional[int]
    ...     b: Optional[str]
    ...     c: Optional[bool]
    >>> class FooUpdateReq(BaseModel):
    ...     a: Optional[int]
    ...     b: Optional[int]
    ...     c: Optional[bool]
    ...     insecure: bool = False
    >>> foo = Foo(a=1, b="foo", c=True)
    >>> # we get a ctx object from Typer inside the function of a command
    >>> ctx = typer.Context(...) # --a 2 --b bar
    >>> foo_update = create_updated_model(foo, FooUpdateReq, ctx)
    >>> foo_update
    FooUpdateReq(a=2, b='bar', c=True, insecure=False)
    >>> #        ^^^  ^^^^^^^
    >>> # We created a FooUpdateReq with the new values from the context

    Parameters
    ----------
    existing : BaseModel
        The existing model to use as a base.
    new : Type[BaseModelType]
        The new model type to construct.
    ctx : typer.Context
        The Typer context to get the updated model parameters from.
    extra : bool
        Whether to include extra fields set on the existing model.
    empty_ok: bool
        Whether to allow the update to be empty. If False, an error will be raised
        if no parameters are provided to update.

    Returns
    -------
    BaseModelType
        The updated model.
    """
    params = model_params_from_ctx(ctx, new)
    if not params and not empty_ok:
        exit_err("No parameters provided to update")

    # Cast existing model to dict, update it with the new values
    d = existing.dict(include=None if extra else existing.__fields_set__)
    d.update(params)

    # Parse it back to the new model
    new_model = new.parse_obj(d)
    return new_model


def parse_harbor_bool_arg(arg: str | None) -> bool | None:
    """Parse a boolean argument for use with Harbor API models
    that have string fields but only accept "true" or "false".

    Parameters
    ----------
    arg : str | None
        The argument to parse.

    Returns
    -------
    bool | None
        The parsed argument. Returns None if the argument is None.
    """
    if arg is None:
        return arg
    if arg.lower() in ["true", "yes", "y"]:
        return True
    elif arg.lower() in ["false", "no", "n"]:
        return False
    else:
        raise ValueError("Cannot parse argument as boolean: {}".format(arg))


def parse_commalist(arg: List[str]) -> List[str]:
    """Parses an argument that can be specified multiple times,
    or as a comma-separated list, into a list of strings.

    `harbor subcmd --arg foo --arg bar,baz`
    will be parsed as: `["foo", "bar", "baz"]`

    Examples
    -------
    >>> parse_commalist(["foo", "bar,baz"])
    ["foo", "bar", "baz"]
    """
    return [item for arg_list in arg for item in arg_list.split(",")]


def parse_key_value_args(arg: list[str]) -> dict[str, str]:
    """Parses a list of key=value arguments.

    Examples
    -------
    >>> parse_key_value_args(["foo=bar", "baz=qux"])
    {'foo': 'bar', 'baz': 'qux'}

    Parameters
    ----------
    arg
        A list of key=value arguments.

    Returns
    -------
    dict[str, str]
        A dictionary mapping keys to values.
    """
    metadata = {}
    for item in arg:
        try:
            key, value = item.split("=", maxsplit=1)
        except ValueError:
            raise typer.BadParameter(
                f"Invalid metadata item {item!r}. Expected format: key=value"
            )
        metadata[key] = value
    return metadata
