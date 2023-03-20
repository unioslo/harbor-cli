from __future__ import annotations

from typing import Any
from typing import Callable
from typing import List
from typing import Type

import pytest

from harbor_cli.types import assert_type
from harbor_cli.types import is_sequence_func


@pytest.mark.parametrize(
    "value, expect_type",
    [
        (["foo"], List[str]),
        ([], List[str]),
        ([], List[Any]),
        ("foo", str),
        (123, int),
        (True, bool),
        (True, Any),
        pytest.param("foo", List[int], marks=pytest.mark.xfail),
    ],
)
def test_assert_type(value: Any, expect_type: Type[Any]) -> None:
    """Test that assert_type raises a TypeError when the value is not of the expected type."""
    assert_type(value, expect_type)


def _func_list() -> List[int]:  # 3.8 compatible
    return [1, 2, 3]


def _func_int() -> int:
    return 123


@pytest.mark.parametrize(
    "func",
    [
        pytest.param(_func_list, id="List[int]"),  # OK
        pytest.param(_func_int, id="int", marks=pytest.mark.xfail),  # FAIL
    ],
)
def test_is_sequence_func(func: Callable[[Any], Any]) -> None:
    """Test that is_sequence_func returns True for functions that return a Sequence."""
    assert is_sequence_func(func)
