from __future__ import annotations

from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

import typer
from pydantic import BaseModel

from ..logs import logger
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
    model : Type[BaseModel]
        The model to get the parameters for.
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
        if key in model.__fields__ and (not filter_none or value is not None)
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
    from ..output.console import exit_err

    params = model_params_from_ctx(ctx, new)
    if not params and not empty_ok:
        exit_err("No parameters provided to update")

    # Cast existing model to dict, update it with the new values
    d = existing.dict(include=None if extra else set(new.__fields__))
    d.update(params)

    return new.parse_obj(d)


def parse_commalist(arg: Optional[List[str]]) -> List[str]:
    """Parses an optional argument that can be specified multiple times,
    or as a comma-separated string, into a list of strings.

    `harbor subcmd --arg foo --arg bar,baz`
    will be parsed as: `["foo", "bar", "baz"]`

    Examples
    -------
    ```py
    >>> parse_commalist(["foo", "bar,baz"])
    ["foo", "bar", "baz"]
    >>> parse_commalist([])
    []
    >>> parse_commalist(None)
    []
    ```
    """
    if arg is None:
        return []
    return [item for arg_list in arg for item in arg_list.split(",")]


def parse_commalist_int(arg: Optional[List[str]]) -> List[int]:
    """Parses a comma-separated list and converts the values to integers."""
    int_list = []
    for item in parse_commalist(arg):
        try:
            int_list.append(int(item))
        except ValueError:
            raise ValueError(f"Invalid integer value: {item!r}")
    return int_list


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


def as_query(**kwargs: Any) -> str:
    """Converts keyword arguments into a query string.

    Always returns a string, even if the resulting query string is empty.

    Examples
    --------
    >>> as_query(foo="bar", baz="qux")
    'foo=bar,baz=qux'
    """
    return ",".join(f"{k}={v}" for k, v in kwargs.items())


# TODO: could we annotate this in a way where at least one value is required?
def construct_query_list(
    *values: Any,
    union: bool = True,
    allow_empty: bool = False,
    comma: bool = False,
) -> str:
    """Given a key and a list of values, returns a harbor API
    query string with values as a list with union or intersection
    relationship (default: union).

    Falsey values are ignored if allow_empty is False (default).

    Examples
    --------
    >>> construct_query_list("foo", "bar", "baz", union=True)
    '{foo bar baz}'
    >>> construct_query_list("foo", "bar", "baz", union=False)
    '(foo bar baz)'
    >>> construct_query_list("", "bar", "baz")
    '{bar baz}'
    >>> construct_query_list("", "bar", "baz", allow_empty=True)
    '{ bar baz}'
    >>> construct_query_list("", "bar", "baz", comma=True)
    '{bar, baz}'
    """
    if len(values) < 2:
        return str(values[0] if values else "")
    start = "{" if union else "("
    end = "}" if union else ")"
    sep = ", " if comma else " "
    return f"{start}{sep.join(str(v) for v in values if v or allow_empty)}{end}"


def deconstruct_query_list(qlist: str) -> list[str]:
    """Given a harbor API query string with values as a list (either union
    and intersection), returns a list of values. Will break if values
    contain spaces.

    Examples
    --------
    >>> deconstruct_query_list("{foo bar baz}")
    ['foo', 'bar', 'baz']
    >>> deconstruct_query_list("(foo bar baz)")
    ['foo', 'bar', 'baz']
    >>> deconstruct_query_list("{}")
    []
    """
    # TODO: add comma support
    values = qlist.strip("{}()").split(" ")
    return [v for v in values if v]


def add_to_query(query: str | None, **kwargs: str | list[str] | None) -> str:
    """Given a query string and a set of keyword arguments, returns a
    new query string with the keyword arguments added to it. Keyword
    arguments that are already present in the query string will be
    overwritten.

    Always returns a string, even if the resulting query string is empty.

    TODO: allow fuzzy matching, e.g. foo=~bar

    Examples
    --------
    >>> add_to_query("foo=bar", baz="qux")
    'foo=bar,baz=qux'
    >>> add_to_query("foo=bar", foo="baz")
    'foo=baz'
    >>> add_to_query(None, foo="baz")
    'foo=baz'
    """
    query_items = parse_commalist([query] if query else [])
    query_dict = parse_key_value_args(query_items)
    for k, v in kwargs.items():
        # Empty string, empty list, None, etc. are all ignored
        if not v:
            continue

        # When the query already has a value for the given key, we need to
        # convert the value to a list if isn't already one.
        # NOTE: not handling empty query lists here, but it's on the user
        # to not pass empty lists.
        if k in query_dict:
            if isinstance(v, list):
                query_dict[k] = construct_query_list(query_dict[k], *v)
            else:
                query_dict[k] = construct_query_list(
                    *deconstruct_query_list(query_dict[k]),
                    v,
                )
        else:  # doesn't exist in query
            if isinstance(v, str):
                query_dict[k] = v
            elif len(v) > 1:
                query_dict[k] = construct_query_list(*v)
            else:
                query_dict[k] = v[0]
    return as_query(**query_dict)


def _get_id_name_arg(
    resource_type: str, resource_name: str | None, resource_id: int | None
) -> str | int:
    """
    Helper function for getting a resource given its name or ID.

    NOTE
    ----
    Why not just a single arg and check if all the characters are digits?
    Because the resource name can be a string of digits, e.g. "1234", so
    just checking if the string is all digits is not sufficient, and would
    break access to those projects.
    """
    if resource_name is None and resource_id is None:
        exit_err(
            f"Must specify either {resource_type} name or project {resource_type}."
        )
    if resource_name is not None and resource_id is not None:
        logger.warning(
            f"{resource_type} name and ID both specified. Ignoring {resource_type} name."
        )
    if resource_id is not None:
        return resource_id
    elif resource_name is not None:
        return resource_name
    else:
        # mypy doesn't like return resource_name if resource_name is not None else resource_name
        raise ValueError("This should never happen")


def get_project_arg(project_name: str | None, project_id: int | None) -> str | int:
    """Given a project name and project ID, returns the one that is not None.
    One of name or ID must be not None. Harbor API expects that int args are
    project IDs and string args are project names.

    The ID will be returned if both are specified."""
    return _get_id_name_arg("project", project_name, project_id)


def get_user_arg(username: str | None, user_id: int | None) -> str | int:
    """Given a project name and project ID, returns the one that is not None.
    One of name or ID must be not None. Harbor API expects that int args are
    user IDs and string args are user names.

    The ID will be returned if both are specified."""
    return _get_id_name_arg("user", username, user_id)


def get_ldap_group_arg(group_dn: str | None, group_id: int | None) -> str | int:
    return _get_id_name_arg("LDAP Group", group_dn, group_id)
