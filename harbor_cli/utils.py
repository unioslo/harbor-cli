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


def inject_help(
    model: type[BaseModel], strict: bool = False, **field_additions: str
) -> Any:
    """
    Injects a Pydantic model's field descriptions into the help attributes
    of Typer.Option() function parameters whose names match the field names.

    Example
    -------
    ```python
    class MyModel(BaseModel):
        my_field: str = Field(..., description="Description of my_field")

    @app.command(name="my-command")
    @inject_help(MyModel)
    def my_command(my_field: str = typer.Option(...)):
        ...

    # `my-app my-command --help`
    # my_field's help text will be "Description of my_field"
    ```

    NOTE
    ----
    Does not modify the help text of options with existing help text!
    Use the `**field_additions` parameter to add additional help text to a field
    in addition to the field's description. This text is appended to the
    help text, separated by a space.

    e.g. `@inject_help(MyModel, my_field="Additional help text that is appended to the field's description.")`

    Parameters
    ----------
    model : type[BaseModel]
        The pydantic model to use for help injection.
    strict : bool
        If True, fail if a field in the model does not have a matching typer
        option, by default False
    **field_additions
        Additional help text to add to the help attribute of a field.
        The parameter name should be the name of the field, and the value
        should be the additional help text to add. This is useful when
        the field's description is not sufficient, and you want to add
        additional help text.
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
                addition = field_additions.get(field_name, "")
                if addition:
                    addition = f" {addition}"  # add leading space
                param.default.help = f"{field.field_info.description}{addition}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


# This injection seems too complicated...?
#
# '--sort' and '-query' are two parameters that are used in many commands
# in order to not have to write out the same code over and over again,
# we can use these decorators to inject the parameters (and their accompanying help text)
# into a function, given that the function has a parameter with the same name,
# (e.g. 'query', 'sort', etc.)
#
# NOTE: we COULD technically inject the parameter even if the function doesn't
# already have it, but that is too magical, and does not play well with
# static analysis tools like mypy.
#
# Fundamentally, we don't want to change the function signature, only set the
# default value of the parameter to a typer.Option() instance.
# This lets Typer pick it up and use it to display help text and create the
# correct commandline option (--query, --sort, etc.)
#
# Unlike most decorators, the function is not wrapped, but rather its
# signature is modified in-place, and then the function is returned.


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


def _patch_param(
    func: Any, name: str, value: typer.models.OptionInfo, strict: bool
) -> Any:
    """Patches a function's parameter with the given name to have the given default value."""
    sig = inspect.signature(func)
    new_params = sig.parameters.copy()  # this copied object is mutable
    to_replace = new_params.get(name)

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

    new_params[name] = to_replace.replace(default=value)
    new_sig = sig.replace(parameters=list(new_params.values()))
    func.__signature__ = new_sig

    return func
