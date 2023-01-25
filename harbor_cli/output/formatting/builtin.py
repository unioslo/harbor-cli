"""Formatting functions for builtin types."""
from __future__ import annotations

from typing import Optional

from .constants import NONE_STR


def bool_str(value: Optional[bool], none_is_false: bool = True) -> str:
    """Format a boolean value as a string."""
    # Harbor API sometimes has None signify False
    # Why? I don't know.
    if value is None and none_is_false:
        value = False
    return str(value if value is not None else NONE_STR).lower()


def float_str(value: Optional[float], precision: int = 2) -> str:
    """Format a float value as a string."""
    if value is None:
        return NONE_STR
    return f"{value:.{precision}f}"


def int_str(value: Optional[int]) -> str:
    """Format an integer value as a string."""
    if value is None:
        return NONE_STR
    return str(value)
