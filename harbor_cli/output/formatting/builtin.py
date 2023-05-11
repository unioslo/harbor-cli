"""Formatting functions for builtin types."""
from __future__ import annotations

from typing import Any
from typing import Optional
from typing import Sequence

from ...state import get_state
from ...style import EMOJI_NO
from ...style import EMOJI_YES
from .constants import FALSE_STR
from .constants import NONE_STR
from .constants import TRUE_STR

state = get_state()


def str_str(value: Optional[str]) -> str:
    """Format an optional string value as a string."""
    return str(value if value is not None else NONE_STR)


def bool_str(value: Optional[bool], none_is_false: bool = True) -> str:
    """Format a boolean value as a string."""
    # Harbor API sometimes has None signify False
    # Why? I don't know.
    if value is None and none_is_false:
        value = False
    if state.config.output.table.style.bool_emoji:
        return EMOJI_YES if value else EMOJI_NO
    elif value is None:
        return NONE_STR  # should we return None in emoji mode as well?
    return TRUE_STR if value else FALSE_STR


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


def plural_str(value: str, sequence: Sequence[Any]) -> str:
    """Format a string as a pluralized string if a given sequence is
    not of length 1."""
    if value.endswith("y"):
        plural_value = value[:-1] + "ies"
    elif value.endswith("ies"):
        plural_value = value
        value = value[:-3] + "y"
    elif value.endswith("s"):
        plural_value = value
        value = value[:-1]
    else:
        plural_value = value + "s"
    return value if len(sequence) == 1 else f"{plural_value}"
