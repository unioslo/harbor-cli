"""Utility functions that can't be neatly categorized, or are so niche
that they don't need their own module."""
from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import MutableMapping
from typing import TypeVar

MappingType = TypeVar("MappingType", bound=MutableMapping[str, Any])


def replace_none(d: MappingType, replacement: Any = "") -> MappingType:
    """Replaces None values in a dict with a given replacement value.
    Iterates recursively through nested dicts and iterables.

    Untested with iterables other than list, tuple, and set.
    """

    if d is None:
        return replacement

    def _try_convert_to_original_type(
        value: Iterable[Any], original_type: type
    ) -> Iterable[Any]:
        """Try to convert an iterable to the original type.
        If the original type cannot be constructed with an iterable as
        the only argument, return a list instead.
        """
        try:
            return original_type(value)
        except TypeError:
            return list(value)

    def _iter_iterable(value: Iterable[Any]) -> Iterable[Any]:
        """Iterates through an iterable recursively, replacing None values."""
        t = type(value)
        v_generator = (item if item is not None else replacement for item in value)
        values = []

        for item in v_generator:
            v = None
            if isinstance(item, MutableMapping):
                v = replace_none(item)
            elif isinstance(item, str):  # don't need to recurse into each char
                v = item  # type: ignore
            elif isinstance(item, Iterable):
                v = _iter_iterable(item)  # type: ignore
            else:
                v = item
            values.append(v)
        if values:
            return _try_convert_to_original_type(values, t)
        else:
            return value

    for key, value in d.items():
        if isinstance(value, MutableMapping):
            d[key] = replace_none(value)
        elif isinstance(value, str):
            d[key] = value
        elif isinstance(value, Iterable):
            d[key] = _iter_iterable(value)
        elif value is None:
            d[key] = replacement
    return d
