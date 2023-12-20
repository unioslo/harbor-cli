from __future__ import annotations

import sys
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
from typing import TYPE_CHECKING
from typing import TypeVar


if TYPE_CHECKING:
    from rich import box
    from rich.console import JustifyMethod
    from rich.style import StyleType
    from rich.text import TextType
    from rich.padding import PaddingDimensions
    from typing import Iterable, TypedDict, Optional

    class RichTableKwargs(TypedDict, total=False):
        caption: Optional[TextType]
        width: Optional[int]
        min_width: Optional[int]
        box: Optional[box.Box]
        safe_box: Optional[bool]
        padding: PaddingDimensions
        collapse_padding: bool
        pad_edge: bool
        expand: bool
        show_header: bool
        show_footer: bool
        show_edge: bool
        show_lines: bool
        leading: int
        style: StyleType
        row_styles: Optional[Iterable[StyleType]]
        header_style: Optional[StyleType]
        footer_style: Optional[StyleType]
        border_style: Optional[StyleType]
        title_style: Optional[StyleType]
        caption_style: Optional[StyleType]
        title_justify: "JustifyMethod"
        caption_justify: "JustifyMethod"
        highlight: bool


T = TypeVar("T")

if sys.version_info >= (3, 10):
    from types import EllipsisType as EllipsisType
else:
    # EllipsisType was introduced in 3.10
    # NOTE: not really sure why mypy doesn't accept type(Ellipsis) as a type...
    EllipsisType = Any

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
