from __future__ import annotations

import sys
from typing import Optional

import typer

from .logs import logger


class Deprecated(str):
    """String type used to mark a parameter as deprecated.

    Acts like a string, but has an extra attribute 'replacement' that
    contains the replacement option (if any)."""

    replacement: Optional[str] = None

    def __new__(cls, s, replacement: str | None = None) -> Deprecated:
        obj = str.__new__(cls, s)
        obj.replacement = replacement
        return obj


# Factored into separate functions for easier testing


def get_deprecated_params(ctx: typer.Context) -> list[Deprecated]:
    """Returnds a list of parameters for a context that have been marked
    as deprecated."""
    info_dict = ctx.to_info_dict()
    params = info_dict["command"]["params"]
    deprected_params = []
    for param in params:
        for opt in param["opts"]:
            if isinstance(opt, Deprecated):
                deprected_params.append(opt)
    return deprected_params


def used_deprecated(ctx: typer.Context) -> list[Deprecated]:
    """Returns a list of deprecated parameters that have been used."""
    deprecated = get_deprecated_params(ctx)
    used = []
    for param in deprecated:
        if param in sys.argv:
            used.append(param)
    return used


def check_deprecated_option(ctx: typer.Context) -> None:
    """Checks if any deprecated options have been used and logs a warning
    for each one."""
    deprecated = used_deprecated(ctx)
    for param in deprecated:
        if param in sys.argv:
            msg = f"Option {param} is deprecated."
            if param.replacement:
                msg += f" Use {param.replacement} instead."
            logger.warning(msg)
