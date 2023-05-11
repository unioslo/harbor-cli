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
from harbor_cli.output.formatting.constants import FALSE_STR
from harbor_cli.output.formatting.constants import TRUE_STR
from harbor_cli.state import get_state
from harbor_cli.style import EMOJI_NO
from harbor_cli.style import EMOJI_YES


state = get_state()


@pytest.mark.parametrize(
    "inp,expected,none_is_false,as_emoji",
    [
        # Text
        (True, TRUE_STR, False, False),
        (False, FALSE_STR, False, False),
        (None, NONE_STR, False, False),
        (None, FALSE_STR, True, False),
        # Emoji
        (True, EMOJI_YES, False, True),
        (False, EMOJI_NO, False, True),
        (None, EMOJI_NO, False, True),
        (None, EMOJI_NO, True, True),
    ],
)
def test_bool_str(
    inp: bool, expected: str, none_is_false: bool, as_emoji: bool
) -> None:
    state.config.output.table.style.bool_emoji = as_emoji
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
        (0, "0"),
        (1, "1"),
        (1234, "1234"),
        (None, NONE_STR),
    ],
)
def test_int_str(inp: int, expected: str) -> None:
    assert int_str(inp) == expected


class SomeModel(BaseModel):
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
        ("model", [SomeModel()], "model"),
        ("model", [SomeModel(), SomeModel()], "models"),
        ("vulnerability", [], "vulnerabilities"),
        ("vulnerability", ["HIGH"], "vulnerability"),
        ("vulnerability", ["HIGH", "LOW"], "vulnerabilities"),
        # Test providing plural form as input
        # "*ies" case
        ("vulnerabilities", [], "vulnerabilities"),
        ("vulnerabilities", ["HIGH"], "vulnerability"),
        ("vulnerabilities", ["HIGH", "LOW"], "vulnerabilities"),
        # "*s" case
        ("models", [], "models"),
        ("models", [SomeModel()], "model"),
        ("models", [SomeModel(), SomeModel()], "models"),
    ],
)
def test_plural_str(s: str, seq: Sequence[Any], expected: str) -> None:
    assert plural_str(s, seq) == expected
