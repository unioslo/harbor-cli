from __future__ import annotations

from typing import Any


def replace_none(d: dict[str, Any], replacement: Any = "") -> dict[str, Any]:
    """Replaces None values in a dict with empty strings.
    Iterates recursively through nested dicts and lists.

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
