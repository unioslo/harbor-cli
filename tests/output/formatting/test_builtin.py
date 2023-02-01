from __future__ import annotations

from typing import Any
from typing import Sequence

import pytest
from harborapi.models.base import BaseModel

from harbor_cli.output.formatting.builtin import bool_str
from harbor_cli.output.formatting.builtin import float_str
from harbor_cli.output.formatting.builtin import int_str
from harbor_cli.output.formatting.builtin import NONE_STR
from harbor_cli.output.formatting.builtin import plural_str


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


class TestModel(BaseModel):
    a: str = "a"
    b: int = 1


@pytest.mark.parametrize(
    "s, seq, expected",
    [
        ("item", [], "items"),
        ("item", [1], "item"),
        ("item", [1, 2], "items"),
        ("letter", "", "letters"),
        ("letter", "a", "letter"),
        ("letter", "ab", "letters"),
        ("model", [], "models"),
        ("model", [TestModel()], "model"),
        ("model", [TestModel(), TestModel()], "models"),
        ("vulnerability", [], "vulnerabilities"),
        ("vulnerability", ["HIGH"], "vulnerability"),
        ("vulnerability", ["HIGH", "LOW"], "vulnerabilities"),
    ],
)
def test_plural_str(s: str, seq: Sequence[Any], expected: str) -> None:
    assert plural_str(s, seq) == expected
