"""Formatting functions for builtin types."""
from __future__ import annotations

from typing import Optional


def bool_str(value: Optional[bool], none_is_false: bool = True) -> str:
    """Format a boolean value as a string."""
    # Harbor API sometimes has None signify False
    # Why? I don't know.
    if value is None and none_is_false:
        value = False
    return str(value if value is not None else "null").lower()
