from __future__ import annotations

import pytest

from harbor_cli.output.formatting.builtin import bool_str
from harbor_cli.output.formatting.builtin import float_str
from harbor_cli.output.formatting.builtin import int_str
from harbor_cli.output.formatting.builtin import NONE_STR


@pytest.mark.parametrize(
    "inp,expected,none_is_false",
    [
        (True, "true", False),
        (False, "false", False),
        (None, NONE_STR, False),
        (None, "false", True),
    ],
)
def test_bool_str(inp: bool, expected: str, none_is_false: bool) -> None:
    assert bool_str(inp, none_is_false) == expected


@pytest.mark.parametrize(
    "inp,expected,precision",
    [
        (1.0, "1.00", 2),
        (1.0, "1.0", 1),
        (1.0, "1", 0),
        (None, NONE_STR, 2),
    ],
)
def test_float_str(inp: float, expected: str, precision: int) -> None:
    assert float_str(inp, precision) == expected


@pytest.mark.parametrize(
    "inp,expected",
    [
        (1, "1"),
        (None, NONE_STR),
    ],
)
def test_int_str(inp: int, expected: str) -> None:
    assert int_str(inp) == expected
