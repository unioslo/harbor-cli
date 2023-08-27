from __future__ import annotations

from typing import Any

import pytest
from harborapi.models.scanner import Severity
from strenum import StrEnum

from harbor_cli.style import color
from harbor_cli.style.color import HealthColor
from harbor_cli.style.color import SeverityColor
from harbor_cli.style.markup import CODEBLOCK_STYLES
from harbor_cli.style.markup import markup_as_plain_text
from harbor_cli.style.markup import markup_to_markdown


@pytest.mark.parametrize(
    "inp,expected",
    [
        # Combinations of no style and bold/italic
        ("", ""),
        ("hello world", "hello world"),
        ("hello [italic]world[/]", "hello *world*"),
        ("hello [italic]world[/italic]", "hello *world*"),
        ("hello [bold]world[/]", "hello **world**"),
        ("hello [bold]world[/bold]", "hello **world**"),
        ("hello [bold italic]world[/]", "hello ***world***"),
        ("hello [bold italic]world[/bold italic]", "hello ***world***"),
        # Overlapping styles (code with bold/italic)
        # IRL this would render as a code block with asterisks in it.
        (
            f"[{CODEBLOCK_STYLES[0]}]hello [bold]world[/bold][/]",
            "`hello **world**`",
        ),
        (
            "[bold]hello[italic] world[/italic][/bold]",
            "**hello* world***",
        ),
        # Causes issues if offset is not handled correctly
        (
            "Type of schedule, e.g. [bold magenta]Hourly[/]. Mutually exclusive with [green]--cron[/].",
            "Type of schedule, e.g. `Hourly`. Mutually exclusive with `--cron`.",
        ),
        # Numerous styles
        (
            "[bold]hello [italic]world[/italic][/bold] [black]foo[/] [bold]bar[/] [bold italic]baz[/]",
            "**hello *world*** foo **bar** ***baz***",
        ),
    ],
)
def test_markup_to_markdown_general(inp: str, expected: str) -> None:
    assert markup_to_markdown(inp) == expected


@pytest.mark.parametrize("style", CODEBLOCK_STYLES)
def test_markup_to_markdown_code_styles(style: str) -> None:
    assert markup_to_markdown(f"[{style}]hello world[/]") == "`hello world`"


def test_markup_to_markdown_emoji() -> None:
    """Test that emoji are converted to unicode characters and play nice when nested inside other styles"""
    s = f":sparkles: [{CODEBLOCK_STYLES[0]}]Hello world :desktop_computer:[/] foo [bold]:sparkles: bar :sparkles:[/] [bold italic]:sparkles: baz :sparkles:[/] :sparkles:"
    assert markup_to_markdown(s) == "✨ `Hello world 🖥` foo **✨ bar ✨** ***✨ baz ✨*** ✨"


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("", ""),
        ("[bold][/]", ""),
        ("[bold][/bold]", ""),
        ("This is a test", "This is a test"),
        ("This is a [bold]test[/]", "This is a test"),
        ("This is a [bold]test[/bold]", "This is a test"),
        ("[italic]This is a [bold]test[/bold][/italic]", "This is a test"),
        ("[italic]This is a [bold]test[/bold][/]", "This is a test"),
    ],
)
def test_markup_as_plain_text(inp: str, expected: str) -> None:
    assert markup_as_plain_text(inp) == expected


@pytest.mark.parametrize(
    "severity,expected",
    [
        (Severity.unknown, SeverityColor.UNKNOWN),
        # (Severity.none, SeverityColor.NONE),
        (Severity.negligible, SeverityColor.NEGLIGIBLE),
        (Severity.low, SeverityColor.LOW),
        (Severity.medium, SeverityColor.MEDIUM),
        (Severity.high, SeverityColor.HIGH),
        (Severity.critical, SeverityColor.CRITICAL),
    ],
)
def test_severitycolor_from_severity(
    severity: Severity, expected: SeverityColor
) -> None:
    # Test using the enum value first
    assert SeverityColor.from_severity(severity) == expected
    # Then as a string
    # The harborapi Severity enum values have a capital first letter
    assert SeverityColor.from_severity(severity.value) == expected


@pytest.mark.parametrize(
    "health,expected",
    [
        ("healthy", HealthColor.HEALTHY),
        ("unhealthy", HealthColor.UNHEALTHY),
        (None, HealthColor.UNHEALTHY),
        ("", HealthColor.UNHEALTHY),
        ("123", HealthColor.UNHEALTHY),
        (123, HealthColor.UNHEALTHY),
    ],
)
def test_healthcolor_from_health(health: Any, expected: SeverityColor) -> None:
    assert HealthColor.from_health(health) == expected


def test_strenum_as_str() -> None:
    """The strenum library should ensure this behavior for us, but
    this is a sanity check to make sure it works as expected."""

    class TestEnum(StrEnum):
        A = "a"
        B = "b"

    assert str(TestEnum.A) == "a"
    assert str(TestEnum.B) == "b"
    assert f"{TestEnum.A}" == "a"
    assert f"{TestEnum.B}" == "b"

    # Real use-case where we construct a Rich markup formatted string with a StrEnum
    assert f"[{TestEnum.A}]foo[/]" == "[a]foo[/]"


@pytest.mark.parametrize(
    "func_name",
    [
        "blue",
        "cyan",
        "green",
        "magenta",
        "red",
        "yellow",
    ],
)
def test_color_func(func_name: str) -> None:
    func = getattr(color, func_name)
    assert func("foo") == f"[{func_name}]foo[/]"
