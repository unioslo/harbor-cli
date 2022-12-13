from __future__ import annotations

import inspect
from functools import wraps
from typing import Any

import typer
from pydantic import BaseModel


def replace_none(d: dict[str, Any], replacement: Any = "") -> dict[str, Any]:
    """Replaces None values in a dict with a given replacement value.
    Iterates recursively through nested dicts.
    Lists of depth 1 are also iterated through.

    Does not support list of dicts yet.
    Does not support containers other than dict and list.
    """
    if d is None:
        return replacement
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = replace_none(value)
        elif isinstance(value, list):
            d[key] = [item if item is not None else replacement for item in value]
        elif value is None:
            d[key] = replacement
    return d


def inject_help(model: type[BaseModel], strict: bool = False) -> Any:
    """
    Injects the description attributes of a pydantic model's fields into the
    help attributes of Typer options with matching names.

    Parameters
    ----------
    model : type[BaseModel]
        The pydantic model to use for help injection.
    strict : bool
        If True, fail if a field in the model does not have a matching typer
        option, by default False
    """

    def decorator(func: Any) -> Any:
        sig = inspect.signature(func)
        for field_name, field in model.__fields__.items():
            # only overwrite help if not already set
            param = sig.parameters.get(field_name, None)
            if not param:
                if strict:
                    raise ValueError(
                        f"Field {field_name!r} not found in function signature of {func.__qualname__!r}."
                    )
                continue
            if not hasattr(param, "default") or not hasattr(param.default, "help"):
                continue
            if not param.default.help:
                param.default.help = field.field_info.description

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


# This injection seems too complicated...?
#
# '--sort' and '-query' are two parameters that are used in many commands
# in order to not have to write out the same code over and over again,
# we can use these decorators to inject the parameters into the function,
# given that the function has a parameter with the same name.
#
# NOTE: we COULD technically inject the parameter even if the function doesn't
# already have it, but that is too magical, and does not play well with
# static analysis tools like mypy.


def inject_query(strict: bool = False) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            None, "--query", help="Query parameters to filter the results. "
        )
        return _patch_param(func, "query", option, strict)

    return decorator


def inject_sort(strict: bool = False) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            None,
            "--sort",
            help="Sorting order of the results. Example: 'name,-id' to sort by name ascending and id descending. ",
        )
        return _patch_param(func, "sort", option, strict)

    return decorator


def _patch_param(func: Any, name: str, param: typer.models.OptionInfo, strict) -> Any:
    sig = inspect.signature(func)
    mutable_params = sig.parameters.copy()
    to_replace = mutable_params.get(name)

    if not to_replace:
        if strict:
            raise ValueError(
                f"Field {name!r} not found in function signature of {func.__qualname__!r}."
            )
        return func

    if not to_replace.annotation:
        raise ValueError(
            f"Parameter {name!r} in function {func.__qualname__!r} must have a type annotation."
        )

    if to_replace.annotation not in ["Optional[str]", "str | None", "None | str"]:
        raise ValueError(
            f"Parameter {name!r} in function {func.__qualname__!r} must be of type 'Optional[str]' or 'str | None'."
        )

    mutable_params[name] = to_replace.replace(default=param)
    new_sig = sig.replace(parameters=list(mutable_params.values()))
    func.__signature__ = new_sig

    return func
