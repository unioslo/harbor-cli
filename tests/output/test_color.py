from __future__ import annotations

import typing
from typing import Tuple

import pytest

from harbor_cli.style.color import Color
from harbor_cli.style.color import COLOR_FUNCTIONS
from harbor_cli.style.color import fallback_color
from harbor_cli.style.color import get_color_func
from harbor_cli.style.color import Severity
from harbor_cli.style.color import SeverityColor


def test_from_severity():
    assert SeverityColor.from_severity("CRITICAL") == SeverityColor.CRITICAL
    assert SeverityColor.from_severity("HIGH") == SeverityColor.HIGH
    assert SeverityColor.from_severity("MEDIUM") == SeverityColor.MEDIUM
    assert SeverityColor.from_severity("LOW") == SeverityColor.LOW
    assert SeverityColor.from_severity("NEGLIGIBLE") == SeverityColor.NEGLIGIBLE
    assert SeverityColor.from_severity("NONE") == SeverityColor.NONE
    assert SeverityColor.from_severity("UNKNOWN") == SeverityColor.UNKNOWN

    assert SeverityColor.from_severity(Severity.critical) == SeverityColor.CRITICAL
    assert SeverityColor.from_severity(Severity.high) == SeverityColor.HIGH
    assert SeverityColor.from_severity(Severity.medium) == SeverityColor.MEDIUM
    assert SeverityColor.from_severity(Severity.low) == SeverityColor.LOW
    assert SeverityColor.from_severity(Severity.negligible) == SeverityColor.NEGLIGIBLE
    assert SeverityColor.from_severity(Severity.none) == SeverityColor.NONE
    assert SeverityColor.from_severity(Severity.unknown) == SeverityColor.UNKNOWN

    assert SeverityColor.from_severity("INVALID") == SeverityColor.UNKNOWN


def test_as_markup():
    # TODO: less hardcoding of the color names perhaps?
    assert SeverityColor.as_markup("CRITICAL") == "[dark_red]CRITICAL[/]"
    assert SeverityColor.as_markup("HIGH") == "[red]HIGH[/]"
    assert SeverityColor.as_markup("MEDIUM") == "[orange3]MEDIUM[/]"
    assert SeverityColor.as_markup("LOW") == "[green]LOW[/]"
    assert SeverityColor.as_markup("NEGLIGIBLE") == "[blue]NEGLIGIBLE[/]"
    assert SeverityColor.as_markup("NONE") == "[white]NONE[/]"
    assert SeverityColor.as_markup("UNKNOWN") == "[white]UNKNOWN[/]"

    assert SeverityColor.as_markup(Severity.critical) == "[dark_red]CRITICAL[/]"
    assert SeverityColor.as_markup(Severity.high) == "[red]HIGH[/]"
    assert SeverityColor.as_markup(Severity.medium) == "[orange3]MEDIUM[/]"
    assert SeverityColor.as_markup(Severity.low) == "[green]LOW[/]"
    assert SeverityColor.as_markup(Severity.negligible) == "[blue]NEGLIGIBLE[/]"
    assert SeverityColor.as_markup(Severity.none) == "[white]NONE[/]"
    assert SeverityColor.as_markup(Severity.unknown) == "[white]UNKNOWN[/]"


def test_assert_color_mapping_parity() -> None:
    """Ensure the `Color` type annotation and `COLOR_FUNCTIONS` dict are in sync."""
    args: Tuple[str] = typing.get_args(Color)
    assert len(args) > 0  # ensure we are iterating over _something_
    assert len(args) == len(COLOR_FUNCTIONS)
    for arg in args:
        assert arg in COLOR_FUNCTIONS


def test_get_color_func_valid() -> None:
    args: Tuple[str] = typing.get_args(Color)
    assert len(args) > 0  # ensure we are iterating over _something_
    for arg in args:
        func = get_color_func(arg)  # type: ignore
        assert func == COLOR_FUNCTIONS[arg]  # type: ignore
        res = func("test")
        assert "]test[/]" in res


def test_get_color_func_invalid(caplog: pytest.LogCaptureFixture) -> None:
    """An invalid color func name simply returns the string as-is."""
    func = get_color_func("INVALID COLOR")  # type: ignore
    assert func == fallback_color  # type: ignore
    # Fallback returns text as-is
    assert func("test") == "test"  # type: ignore
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "ERROR"
    assert "Invalid color:" in record.message
    # Ensure the stacklevel=2 logging call logs the caller of get_color_func,
    # rather than get_color_func itself.
    assert "test_color.py" in record.filename
