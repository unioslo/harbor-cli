from __future__ import annotations

from typing import NamedTuple
from typing import Sequence

import yaml  # type: ignore
from common import DATA_PATH
from rich.markup import render
from rich.text import Text

from harbor_cli.main import app
from harbor_cli.style import STYLE_CONFIG_OPTION
from harbor_cli.utils.commands import get_app_callback_options


def text_as_md(text: Text) -> str:
    """Very primitive function for rendering a Rich.text.Text span as a
    markdown code span. Can be moved into the main codebase if needed."""
    if not text.spans:
        return text.plain
    for span in text.spans:
        if span.style != STYLE_CONFIG_OPTION:
            continue
        start, stop = span.start, span.end
        p = text.plain
        return p[:start] + f"`{p[start:stop]}`" + p[stop:]
    return text.plain


def maybe_list_to_str(text: str | list[str] | None) -> str:
    if isinstance(text, str) or text is None:
        return str(text)
    return ", ".join(text)


class OptionInfo(NamedTuple):
    params: Sequence[str]
    help: Text | None
    envvar: str | list[str] | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "params": ", ".join(f"`{p}`" for p in self.params),
            "help": text_as_md(self.help) if self.help else None,
            "envvar": maybe_list_to_str(self.envvar),
        }


if __name__ == "__main__":
    options = []  # type: list[OptionInfo]
    for option in get_app_callback_options(app):
        if not option.param_decls:
            continue
        options.append(
            OptionInfo(
                params=option.param_decls,
                help=render(option.help) if option.help else None,
                envvar=option.envvar,
            )
        )

    to_dump = [o.to_dict() for o in options]

    with open(DATA_PATH / "options.yaml", "w") as f:
        yaml.dump(to_dump, f, sort_keys=False)
