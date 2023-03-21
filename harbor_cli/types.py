from __future__ import annotations

import typing
from collections import abc
from typing import Any
from typing import Callable
from typing import cast
from typing import List
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Type
from typing import TypeVar


T = TypeVar("T")

SEQUENCE_TYPES = (Sequence, abc.Sequence, list, List, tuple, Tuple, set, Set)


def is_sequence_func(func: Callable[[Any], Any]) -> bool:
    """Checks if a callable takes a sequence as its first argument."""
    hints = typing.get_type_hints(func)
    if not hints:
        return False
    val = next(iter(hints.values()))
    return is_sequence_annotation(val)


def is_sequence_annotation(annotation: Any) -> bool:
    # A string annotation will never pass this check, since it can't be
    # used as a generic type annotation. get_origin() will return None.
    # This is fine, however, because we don't actually want to treat
    # string annotations as sequences in this context anyway.
    origin = typing.get_origin(annotation)
    try:
        return issubclass(origin, Sequence)  # type: ignore
    except TypeError:
        return origin in SEQUENCE_TYPES


def assert_type(value: Any, expect_type: Type[T]) -> T:
    """Assert that a value is of a given type.

    Not to be confused with typing.assert_type which was introcduced in 3.11!
    Unfortunate naming collision, but typing.assert_type has no runtime effect,
    while this function has."""
    # TODO: handle Union types
    if is_sequence_annotation(expect_type):
        if value:
            v = value[0]
            args = typing.get_args(expect_type)
            if args:
                t = args[0]
            else:
                t = Any  # annotation was generic with no args
        else:
            v = value
            t = typing.get_origin(expect_type)
    else:
        v = value
        t = expect_type

    # If we find no annotation, we treat it as Any
    if t is None:
        t = Any

    if t != Any and not isinstance(v, t):
        raise TypeError(f"Expected value of type {t} but got {type(v)} instead.")
    return cast(T, value)
