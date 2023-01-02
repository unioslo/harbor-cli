from __future__ import annotations

import inspect
from typing import Any
from typing import Type

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


def parse_commalist(arg: list[str]) -> list[str]:
    """Parses an argument that can be specified multiple times,
    or as a comma-separated list, into a list of strings.

    Example:
    my_app --arg foo --arg bar,baz
    will be parsed as: ["foo", "bar", "baz"]
    """
    return [item for arg_list in arg for item in arg_list.split(",")]


def parse_key_value_args(arg: list[str]) -> dict[str, str]:
    """Parses a list of key=value arguments.

    Example
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


def inject_help(
    model: Type[BaseModel], strict: bool = False, **field_additions: str
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
    model : Type[BaseModel]
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
        return func

    return decorator


# NOTE: This injection seems too complicated...? Could maybe just create default
# typer.Option() instances for each field in the model and use them as defaults?

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


def inject_resource_options(
    f: Any = None, *, strict: bool = False, use_defaults: bool = True
) -> Any:
    """Decorator that calls inject_query, inject_sort, inject_page_size,
    inject_page and inject_retrieve_all to inject typer.Option() defaults
    for common options used when querying multiple resources.

    NOTE: needs to be specified BEFORE @app.command() in order to work!

    Not strict by default, so that it can be used on functions that only
    have a subset of the parameters (e.g. only query and sort).

    The decorated function should always declare the parameters in the following order
    if the parameters don't have defaults:
    `query`, `sort`, `page`, `page_size`, `retrieve_all`



    Parameters
    ----------
    f : Any, optional
        The function to decorate, by default None
    strict : bool, optional
        If True, fail if a field in the model does not have a matching typer
        option, by default False
    use_defaults : bool, optional
        If True, use the default value specified by a parameter's typer.Option() field
        as the default value for the parameter, by default True.

        Example:
        @inject_resource_options(use_defaults=True)
        my_func(page_size: int = typer.Option(20)) -> None: ...

        If use_defaults is True, the default value of page_size will be 20,
        instead of 10, which is the value inject_page_size() would use by default.
        NOTE: Only accepts defaults specified via typer.Option() and
        typer.Argument() instances!

        @inject_resource_options(use_default=True)
        my_func(page_size: int = 20) -> None: ... # will fail (for now)

    Returns
    -------
    Any
        The decorated function


    Example
    -------
    ```python
    @app.command()
    @inject_resource_options()
    def my_command(query: str, sort: str, page: int, page_size: int, retrieve_all: bool):
        ...

    # OK
    @app.command()
    @inject_resource_options()
    def my_command(query: str, sort: str):
        ...

    # NOT OK (missing all required parameters)
    @app.command()
    @inject_resource_options(strict=True)
    def my_command(query: str, sort: str):
        ...

    # OK (inherits defaults)
    @app.command()
    @inject_resource_options()
    def my_command(query: str, sort: str, page: int = typer.Option(1)):
        ...

    # NOT OK (syntax error [non-default param after param with default])
    # Use ellipsis to specify unset defaults
    @app.command()
    @inject_resource_options()
    def my_command(query: str = typer.Option("tag=latest"), sort: str, page: int):

    # OK (inherit default query, but override others)
    # Use ellipsis to specify unset defaults
    @app.command()
    @inject_resource_options()
    def my_command(query: str = typer.Option("my-query"), sort: str = ..., page: int = ...):
    ```
    """

    # TODO: add check that the function signature is in the correct order
    # so we don't raise a cryptic error message later on!

    def decorator(func: Any) -> Any:
        # Inject in reverse order, because parameters with defaults
        # can't be followed by parameters without defaults
        func = inject_retrieve_all(func, strict=strict, use_default=use_defaults)
        func = inject_page_size(func, strict=strict, use_default=use_defaults)
        func = inject_page(func, strict=strict, use_default=use_defaults)
        func = inject_sort(func, strict=strict, use_default=use_defaults)
        func = inject_query(func, strict=strict, use_default=use_defaults)
        return func

    # Support using plain @inject_resource_options or @inject_resource_options()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_query(
    f: Any = None, *, strict: bool = False, use_default: bool = True
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            None, "--query", help="Query parameters to filter the results. "
        )
        return _patch_param(func, "query", option, strict, use_default)

    # Support using plain @inject_query or @inject_query()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_sort(
    f: Any = None, *, strict: bool = False, use_default: bool = True
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            None,
            "--sort",
            help="Sorting order of the results. Example: [green]'name,-id'[/] to sort by name ascending and id descending. ",
        )
        return _patch_param(func, "sort", option, strict, use_default)

    # Support using plain @inject_sort or @inject_sort()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_page_size(
    f: Any = None, *, strict: bool = False, use_default: bool = True
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            10,
            "--page-size",
            help="(Advanced) Number of results to fetch per API call. ",
        )
        return _patch_param(func, "page_size", option, strict, use_default)

    # Support using plain @inject_page_size or @inject_page_size()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_page(
    f: Any = None, *, strict: bool = False, use_default: bool = True
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            1, "--page", help="(Advanced) Page to begin fetching from. "
        )
        return _patch_param(func, "page", option, strict, use_default)

    # Support using plain @inject_page or @inject_page()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_retrieve_all(
    f: Any = None, *, strict: bool = False, use_default: bool = False
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            True,
            "--all",
            help="(Advanced) Fetch all matches instead of only first <page_size> matches. ",
        )
        return _patch_param(func, "retrieve_all", option, strict, use_default)

    # Support using plain @inject_page or @inject_page()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def _patch_param(
    func: Any,
    name: str,
    value: typer.models.OptionInfo,
    strict: bool,
    use_default: bool,
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

    # if not to_replace.annotation:
    #     raise ValueError(
    #         f"Parameter {name!r} in function {func.__qualname__!r} must have a type annotation."
    #     )

    # if to_replace.annotation not in ["Optional[str]", "str | None", "None | str"]:
    #     raise ValueError(
    #         f"Parameter {name!r} in function {func.__qualname__!r} must be of type 'Optional[str]' or 'str | None'."
    #     )
    if use_default and hasattr(to_replace.default, "default"):
        value.default = to_replace.default.default
    new_params[name] = to_replace.replace(default=value)
    new_sig = sig.replace(parameters=list(new_params.values()))
    func.__signature__ = new_sig

    return func
