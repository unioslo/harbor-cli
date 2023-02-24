"""Module for generating compact tables for output.

The full tables are automatically generated by the harborapi models, so
we are only concerned with the compact tables here.

A compact table is a table that displays multiple instances of a model
in a single table, rather than one table for each instance (which is what
the full tables do).

Compact tables do not display all of the fields of a model, but only
those that are deemed most relevant to the user.

A compact table is generated by a render function, which is a function
that takes in a harborapi model instance or list of instances and returns
a rich.table.Table object.
"""
from __future__ import annotations

import typing
from collections import abc
from typing import Any
from typing import Callable
from typing import List
from typing import Sequence
from typing import Type
from typing import TypeVar
from typing import Union

from harborapi.ext.artifact import ArtifactInfo
from harborapi.models import Artifact
from harborapi.models import AuditLog
from harborapi.models import Project
from harborapi.models import RegistryProviders
from harborapi.models import Repository
from harborapi.models import Search
from harborapi.models import SystemInfo
from harborapi.models import UserResp
from harborapi.models import UserSearchRespItem
from harborapi.models.scanner import HarborVulnerabilityReport
from rich.panel import Panel
from rich.table import Table

from ...logs import logger
from ...models import BaseModel
from ...models import CommandSummary
from ...models import ProjectExtended
from ...utils._types import is_builtin_obj
from .anysequence import AnySequence
from .anysequence import anysequence_table
from .artifact import artifact_table
from .artifact import artifact_vulnerabilities_table
from .artifact import artifactinfo_panel
from .artifact import artifactinfo_table
from .auditlog import auditlog_table
from .commandsummary import commandsummary_table
from .project import project_extended_panel
from .project import project_table
from .registry import registryproviders_table
from .repository import repository_table
from .search import search_panel
from .system import systeminfo_table
from .user import userresp_table
from .user import usersearchrespitem_table

T = TypeVar("T")

_RENDER_FUNC_SEQ = Callable[[Sequence[T]], Union[Table, Panel]]
_RENDER_FUNC_SINGLE = Callable[[T], Union[Table, Panel]]
RENDER_FUNC_T = Union[_RENDER_FUNC_SEQ, _RENDER_FUNC_SINGLE]


_RENDER_FUNCTIONS = [
    anysequence_table,
    artifactinfo_table,
    artifactinfo_panel,
    artifact_table,
    auditlog_table,
    commandsummary_table,
    artifact_vulnerabilities_table,
    project_table,
    project_extended_panel,
    repository_table,
    systeminfo_table,
    search_panel,
    userresp_table,
    usersearchrespitem_table,
    registryproviders_table,
]  # type: list[RENDER_FUNC_T]

RENDER_FUNCTIONS = {}  # dict of functions + type of first argument
for function in _RENDER_FUNCTIONS:
    hints = typing.get_type_hints(function)
    if not hints:
        continue
    val = next(iter(hints.values()))
    try:
        RENDER_FUNCTIONS[val] = function
    except TypeError:
        logger.warning("Could not add render function %s", function)

# RENDER_FUNCTIONS = {
#     AnySequence: anysequence_table,
#     ArtifactInfo: artifactinfo_table,
#     Artifact: artifact_table,
#     AuditLog: auditlog_table,
#     CommandSummary: commandsummary_table,
#     HarborVulnerabilityReport: artifact_vulnerabilities_table,
#     Project: project_table,
#     ProjectExtended: project_extended_panel,
#     Repository: repository_table,
#     SystemInfo: systeminfo_table,
#     Search: search_panel,
#     UserResp: userresp_table,
#     UserSearchRespItem: usersearchrespitem_table,
#     RegistryProviders: registryproviders_table,
# }  # type: dict[type, Callable[[Any], Table | Panel]]
# # TODO: improve type annotation of this dict


class BuiltinTypeException(TypeError):
    pass


class EmptySequenceError(ValueError):
    pass


def is_sequence_func(func: Callable[[Any], Any]) -> bool:
    hints = typing.get_type_hints(func)
    if not hints:
        return False
    val = next(iter(hints.values()))
    origin = typing.get_origin(val)
    return origin in [Sequence, abc.Sequence, list, List]


def get_render_function(
    obj: T | Sequence[T],
) -> RENDER_FUNC_T:
    """Get the render function for a given object."""

    if isinstance(obj, Sequence):
        if len(obj) == 0:
            raise EmptySequenceError("Cannot render empty sequence.")
        t = Sequence[type(obj[0])]  # type: ignore # TODO: fix this
    else:
        t = type(obj)

    def _get_render_func(t: Type[T]) -> RENDER_FUNC_T:
        try:
            return RENDER_FUNCTIONS[t]
        except KeyError:
            if is_builtin_obj(t):
                raise BuiltinTypeException(
                    "Builtin types cannot be rendered as a compact table."
                )
            raise NotImplementedError(f"{type(obj)} not implemented.")

    try:
        return _get_render_func(t)
    except NotImplementedError:
        return _get_render_func(Sequence[t])  # type: ignore


def get_renderable(obj: T | Sequence[T], **kwargs: Any) -> Table | Panel:
    """Get the renderable for a given object."""
    render_function = get_render_function(obj)
    if is_sequence_func(render_function) and not isinstance(obj, Sequence):
        return render_function([obj], **kwargs)
    return render_function(obj, **kwargs)  # type: ignore
