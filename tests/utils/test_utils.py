from __future__ import annotations

from typing import Any

import pytest

from harbor_cli.utils.utils import replace_none


@pytest.mark.parametrize(
    "d,expected",
    [
        (
            {},
            {},
        ),
        (
            {"a": {}},
            {"a": {}},
        ),
        (
            {"a": "hello world", "b": {"foo": "bar", "baz": None}},
            {"a": "hello world", "b": {"foo": "bar", "baz": ""}},
        ),
        (
            {"a": {"foo": "bar", "baz": None}},
            {"a": {"foo": "bar", "baz": ""}},
        ),
        (
            {"a": None},
            {"a": ""},
        ),
        (
            {"a": 1, "b": None},
            {"a": 1, "b": ""},
        ),
        (
            {"a": 1, "b": None, "c": {"d": None, "e": 4}},
            {"a": 1, "b": "", "c": {"d": "", "e": 4}},
        ),
    ],
)
def test_replace_none(d: dict[str, Any], expected: dict[str, Any]) -> None:
    assert replace_none(d) == expected


# NOTE: sets can't contain dicts, so we don't test them here
@pytest.mark.parametrize(
    "inp,expected",
    [
        (
            {"a": 1, "b": [{"c": 2}, {"d": None}]},
            {"a": 1, "b": [{"c": 2}, {"d": ""}]},
        ),
        (
            {"a": 1, "b": ({"c": 2}, {"d": None})},
            {"a": 1, "b": ({"c": 2}, {"d": ""})},
        ),
        (
            # deeply nested list
            {"a": 1, "b": [[[{"c": 2}, {"d": None}]]]},
            {"a": 1, "b": [[[{"c": 2}, {"d": ""}]]]},
        ),
        (
            # deeply nested tuple
            {"a": 1, "b": ((({"c": 2}, {"d": None})))},
            {"a": 1, "b": (((({"c": 2}, {"d": ""}))))},
        ),
    ],
)
def test_replace_none_iterable_of_dict(
    inp: dict[str, Any], expected: dict[str, Any]
) -> None:

    assert replace_none(inp) == expected


@pytest.mark.parametrize("iterable_type", [list, tuple, set])
def test_replace_none_iterable(iterable_type: type) -> None:
    d = {
        "a": 1,
        "b": iterable_type([2, None, "foo", 3.14]),
        "c": {"d": iterable_type([None, 3, "foo", 3.14]), "e": 4},
    }
    expected = {
        "a": 1,
        "b": iterable_type([2, "", "foo", 3.14]),
        "c": {"d": iterable_type(["", 3, "foo", 3.14]), "e": 4},
    }

    assert replace_none(d) == expected


@pytest.mark.parametrize(
    "replacement",
    ["", 0, False, None],
)
def test_replace_none_replacement(replacement: Any) -> None:
    assert replace_none(None, replacement=replacement) == replacement  # type: ignore
