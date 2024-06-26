"""Monkeypatches Typer to extend certain functionality and change the
styling of its output.

Will probably break for some version of Typer at some point."""

from __future__ import annotations

import inspect
from typing import Iterable
from typing import Union

import click
import typer

from harbor_cli._patches.common import get_patcher

patcher = get_patcher(f"Typer version: {typer.__version__}")


def patch_help_text_style() -> None:
    """Remove dimming of help text.

    https://github.com/tiangolo/typer/issues/437#issuecomment-1224149402
    """
    with patcher("typer.rich_utils.STYLE_HELPTEXT"):
        typer.rich_utils.STYLE_HELPTEXT = ""  # type: ignore


def patch_help_text_spacing() -> None:
    """Adds a single blank line between short and long help text of a command
    when using `--help`.

    As of Typer 0.9.0, the short and long help text is printed without any
    blank lines between them. This is bad for readability (IMO).
    """
    from rich.console import group
    from rich.markdown import Markdown
    from rich.text import Text
    from typer.rich_utils import DEPRECATED_STRING
    from typer.rich_utils import MARKUP_MODE_MARKDOWN
    from typer.rich_utils import MARKUP_MODE_RICH
    from typer.rich_utils import STYLE_DEPRECATED
    from typer.rich_utils import STYLE_HELPTEXT
    from typer.rich_utils import STYLE_HELPTEXT_FIRST_LINE
    from typer.rich_utils import MarkupMode
    from typer.rich_utils import _make_rich_rext  # type: ignore

    @group()
    def _get_help_text(
        *,
        obj: Union[click.Command, click.Group],
        markup_mode: MarkupMode,
    ) -> Iterable[Union[Markdown, Text]]:
        """Build primary help text for a click command or group.

        Returns the prose help text for a command or group, rendered either as a
        Rich Text object or as Markdown.
        If the command is marked as deprecated, the deprecated string will be prepended.
        """
        # Prepend deprecated status
        if obj.deprecated:
            yield Text(DEPRECATED_STRING, style=STYLE_DEPRECATED)

        # Fetch and dedent the help text
        help_text = inspect.cleandoc(obj.help or "")

        # Trim off anything that comes after \f on its own line
        help_text = help_text.partition("\f")[0]

        # Get the first paragraph
        first_line = help_text.split("\n\n")[0]
        # Remove single linebreaks
        if markup_mode != MARKUP_MODE_MARKDOWN and not first_line.startswith("\b"):
            first_line = first_line.replace("\n", " ")
        yield _make_rich_rext(
            text=first_line.strip(),
            style=STYLE_HELPTEXT_FIRST_LINE,
            markup_mode=markup_mode,
        )

        # Get remaining lines, remove single line breaks and format as dim
        remaining_paragraphs = help_text.split("\n\n")[1:]
        if remaining_paragraphs:
            if markup_mode != MARKUP_MODE_RICH:
                # Remove single linebreaks
                remaining_paragraphs = [
                    (
                        x.replace("\n", " ").strip()
                        if not x.startswith("\b")
                        else "{}\n".format(x.strip("\b\n"))
                    )
                    for x in remaining_paragraphs
                ]
                # Join back together
                remaining_lines = "\n".join(remaining_paragraphs)
            else:
                # Join with double linebreaks if markdown
                remaining_lines = "\n\n".join(remaining_paragraphs)
            yield _make_rich_rext(
                text="\n",
                style=STYLE_HELPTEXT,
                markup_mode=markup_mode,
            )
            yield _make_rich_rext(
                text=remaining_lines,
                style=STYLE_HELPTEXT,
                markup_mode=markup_mode,
            )

    with patcher("typer.rich_utils._get_help_text"):
        typer.rich_utils._get_help_text = _get_help_text  # type: ignore


def patch() -> None:
    """Apply all patches."""
    patch_help_text_style()
    patch_help_text_spacing()
