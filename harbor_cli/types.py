from __future__ import annotations

import typing
from collections import abc
from typing import Any
from typing import Callable
from typing import cast
from typing import List
from typing import Sequence
from typing import Type
from typing import TypeVar


T = TypeVar("T")


def is_sequence_func(func: Callable[[Any], Any]) -> bool:
    hints = typing.get_type_hints(func)
    if not hints:
        return False
    val = next(iter(hints.values()))
    return is_sequence_annotation(val)


def is_sequence_annotation(annotation: Any) -> bool:
    origin = typing.get_origin(annotation)
    return origin in [Sequence, abc.Sequence, list, List]


def assert_type(value: Any, expect_type: Type[T]) -> T:
    """Assert that a value is of a given type."""
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
    if t != Any and not isinstance(v, t):
        raise TypeError(f"Expected value of type {t} but got {type(v)} instead.")
    return cast(T, value)
