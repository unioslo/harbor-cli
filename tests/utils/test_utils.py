from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from harbor_cli.config import HarborCLIConfig
from harbor_cli.utils.utils import PackageVersion
from harbor_cli.utils.utils import parse_version_string
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


@pytest.mark.parametrize(
    "package,expected",
    [
        (
            "harbor-cli",
            PackageVersion(package="harbor-cli", min_version=None, max_version=None),
        ),
        (
            "harbor-cli>=0.1.0",
            PackageVersion(package="harbor-cli", min_version="0.1.0", max_version=None),
        ),
        (
            "harbor-cli>=0.1.0, <=1.0.0",
            PackageVersion(
                package="harbor-cli", min_version="0.1.0", max_version="1.0.0"
            ),
        ),
    ],
)
def test_parse_version_string(package: str, expected: PackageVersion) -> None:
    assert parse_version_string(package) == expected
