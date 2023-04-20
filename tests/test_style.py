from __future__ import annotations

import pytest

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
        # Overlapping styles fail
        pytest.param(
            f"[{CODEBLOCK_STYLES[0]}]hello [bold]world[/bold][/]",
            "`hello **world**`",
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            "[bold]hello[italic] world[/italic][/bold]",
            "**hello *world***",
            marks=pytest.mark.xfail,
        ),
        # Causes issues if offset is not handled correctly
        (
            "Type of schedule, e.g. [bold magenta]Hourly[/]. Mutually exclusive with [green]--cron[/].",
            "Type of schedule, e.g. `Hourly`. Mutually exclusive with `--cron`.",
        ),
        # Numerous styles
        pytest.param(
            "[bold]hello [italic]world[/italic][/bold] [black]foo[/] [bold]bar[/] [bold italic]baz[/]",
            "**hello *world*** foo **bar** ***baz***",
            marks=pytest.mark.xfail,
        ),
    ],
)
def test_markup_to_markdown_general(inp: str, expected: str) -> None:
    assert markup_to_markdown(inp) == expected


@pytest.mark.parametrize("style", CODEBLOCK_STYLES)
def test_markup_to_markdown_code_styles(style: str) -> None:
    assert markup_to_markdown(f"[{style}]hello world[/]") == "`hello world`"


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
