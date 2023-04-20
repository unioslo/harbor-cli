from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text

from .style import STYLE_CLI_COMMAND
from .style import STYLE_CLI_OPTION
from .style import STYLE_CLI_VALUE
from .style import STYLE_CONFIG_OPTION

CODEBLOCK_STYLES = [
    STYLE_CLI_OPTION,
    STYLE_CONFIG_OPTION,
    STYLE_CLI_VALUE,
    STYLE_CLI_COMMAND,
]


@dataclass
class MarkdownSpan:
    start: int
    end: int
    italic: bool = False
    bold: bool = False
    code: bool = False


def markup_to_markdown(s: str) -> str:
    """Parses a string that might contain markup formatting and converts it to Markdown.

    This is a very naive implementation that only supports a subset of Rich markup, but it's
    good enough for our purposes.


    !!! warning
        This function does not support combined and/or styles,
        e.g. `[bold italic]foo[/]`, `[bold]foo[italic]bar[/italic][/bold]`, etc.
    """
    # TODO: support combined styles like [bold italic]foo[/]
    # Will probably need to use recursion to handle nested styles (?)
    t = Text.from_markup(s)
    spans = []
    # Markdown has more limited styles than Rich markup, so we just
    # identify the ones we care about and ignore the rest.
    for span in t.spans:
        new_span = MarkdownSpan(span.start, span.end)
        span_style = str(span.style)
        if span_style in CODEBLOCK_STYLES:
            new_span.code = True
        if "italic" in span_style:
            new_span.italic = True
        if "bold" in span_style:
            new_span.bold = True
        spans.append(new_span)

    def _insert(start: int, end: int, char: str, offset: int) -> int:
        new.insert(start + offset, char)
        new.insert(end + 1 + offset, char)  # +1 to insert AFTER
        return offset + (len(char) * 2)

    new = list(str(t.plain))
    offset = 0
    for sp in spans:
        char = []
        # TODO: keep order of styles
        if sp.code:
            char.append("`")

        # Code styles are mutually exclusive with bold/italic for now
        if not sp.code:
            if sp.italic:
                char.append("*")
            if sp.bold:
                char.append("**")

        c = "".join(char)
        offset = _insert(sp.start, sp.end, c, offset)

    return "".join(new)


def markup_as_plain_text(s: str) -> str:
    """Renders a string that might contain markup formatting as a plain text string."""
    return Text.from_markup(s).plain
