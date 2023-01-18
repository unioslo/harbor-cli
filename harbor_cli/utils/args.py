from __future__ import annotations

from typing import Any
from typing import List
from typing import Type

import typer
from pydantic import BaseModel


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

    Examples
    -------
    `my_app --arg foo --arg bar,baz`
    will be parsed as: `["foo", "bar", "baz"]`
    """
    return [item for arg_list in arg for item in arg_list.split(",")]
