from __future__ import annotations

import inspect
from typing import Any
from typing import Type
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..state import State  # noqa

import click
import typer
from pydantic import BaseModel

from ..style import STYLE_CLI_OPTION

from ..output.prompts import bool_prompt

from ..models import CommandSummary


def get_parent_ctx(
    ctx: typer.Context | click.core.Context,
) -> typer.Context | click.core.Context:
    """Get the top-level parent context of a context."""
    if ctx.parent is None:
        return ctx
    return get_parent_ctx(ctx.parent)


def get_command_help(command: typer.models.CommandInfo) -> str:
    """Get the help text of a command."""
    if command.help:
        return command.help
    if command.callback and command.callback.__doc__:
        return command.callback.__doc__.strip().splitlines()[0]
    return ""


# TODO: apparently we can just refactor this to use typer.Context.to_info_dict()?
#       We have to construct a new context to get the help text though
def get_app_commands(
    app: typer.Typer, cmds: list[CommandSummary] | None = None, current: str = ""
) -> list[CommandSummary]:
    if cmds is None:
        cmds = []

    # If we have subcommands, we need to go deeper.
    for group in app.registered_groups:
        if not group.typer_instance:
            continue
        t = group.typer_instance
        if current == "":
            # Prioritize direct name of typer instance over group name (?)
            new_current = t.info.name or group.name
            if isinstance(new_current, typer.models.DefaultPlaceholder):
                new_current = new_current.value
            new_current = new_current or ""  # guarantee not None
        else:
            new_current = f"{current} {t.info.name or ''}"
        get_app_commands(t, cmds, current=new_current)

    # When we have commands, we don't need to go deeper and are done.
    # We can now construct the CommandSummary objects.
    for command in app.registered_commands:
        if not command.name:
            continue
        if current:
            name = f"{current} {command.name}"
        else:
            name = command.name
        cmds.append(CommandSummary(name=name, help=get_command_help(command)))

    return sorted(cmds, key=lambda x: x.name)


def get_app_callback_options(app: typer.Typer) -> list[typer.models.OptionInfo]:
    """Get the options of the main callback of a Typer app."""
    options = []  # type: list[typer.models.OptionInfo]

    if not app.registered_callback:
        return options

    callback = app.registered_callback.callback

    if not callback:
        return options
    if not hasattr(callback, "__defaults__") or not callback.__defaults__:
        return options

    for option in callback.__defaults__:
        options.append(option)
    return options


def check_enumeration_options(
    state: State,
    query: str | None = None,
    limit: int | None = None,
) -> None:
    if state.config.output.confirm_enumeration and (not limit or not query):
        if not bool_prompt(
            f"Neither [{STYLE_CLI_OPTION}]--query[/] nor [{STYLE_CLI_OPTION}]--limit[/] is specified. "
            "This could result in a large amount of data being returned. "
            "Do you want to continue?",
            warning=True,
        ):
            exit()


def inject_help(
    model: Type[BaseModel], strict: bool = False, **field_additions: str
) -> Any:
    """
    Injects a Pydantic model's field descriptions into the help attributes
    of Typer.Option() function parameters whose names match the field names.

    Examples
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
        additional help text to supplement the existing description.
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
                param.default.help = f"{field.field_info.description or ''}{addition}"
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
    inject_page and inject_limit to inject typer.Option() defaults
    for common options used when querying multiple resources.

    NOTE: needs to be specified BEFORE @app.command() in order to work!

    Not strict by default, so that it can be used on functions that only
    have a subset of the parameters (e.g. only query and sort).

    The decorated function should always declare the parameters in the following order
    if the parameters don't have defaults:
    `query`, `sort`, `page`, `page_size`, `limit`

    Examples
    -------
    ```python
    @app.command()
    @inject_resource_options()
    def my_command(query: str, sort: str, page: int, page_size: int, limit: Optional[int]):
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

    Parameters
    ----------
    f : Any, optional
        The function to decorate, by default None
    strict : bool, optional
        If True, fail if function is missing any of the injected parameters, by default False
        E.g. all of `query`, `sort`, `page`, `page_size`, `limit` must be present
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
    """

    # TODO: add check that the function signature is in the correct order
    # so we don't raise a cryptic error message later on!

    def decorator(func: Any) -> Any:
        # Inject in reverse order, because parameters with defaults
        # can't be followed by parameters without defaults
        func = inject_limit(func, strict=strict, use_default=use_defaults)
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
            None, "--query", help="Query parameters to filter the results."
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
            help="Sorting order of the results. Example: [green]'name,-id'[/] to sort by name ascending and id descending.",
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
            help="(Advanced) Number of results to fetch per API call.",
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
            1, "--page", help="(Advanced) Page to begin fetching from."
        )
        return _patch_param(func, "page", option, strict, use_default)

    # Support using plain @inject_page or @inject_page()
    if callable(f):
        return decorator(f)
    else:
        return decorator


def inject_limit(
    f: Any = None, *, strict: bool = False, use_default: bool = False
) -> Any:
    def decorator(func: Any) -> Any:
        option = typer.Option(
            None,
            "--limit",
            help="Maximum number of results to fetch.",
        )
        return _patch_param(func, "limit", option, strict, use_default)

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

    # Use defaults from the injected parameter if they exist
    if use_default:
        if hasattr(to_replace.default, "default"):
            value.default = to_replace.default.default
        if hasattr(to_replace.default, "help") and to_replace.default.help:
            value.help = to_replace.default.help

    new_params[name] = to_replace.replace(default=value)
    new_sig = sig.replace(parameters=list(new_params.values()))
    func.__signature__ = new_sig

    return func
