from __future__ import annotations

import inspect
from functools import wraps
from typing import Any

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


# inject help fields
def inject_help(model: type[BaseModel], strict: bool = False) -> Any:
    """
    Injects the description attributes of a pydantic model's fields into the
    help attributes of typer options with matching names.

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
