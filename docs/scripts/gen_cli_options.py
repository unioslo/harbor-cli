from __future__ import annotations

from typing import NamedTuple

import yaml  # type: ignore
from common import DATA_PATH
from rich.markup import render
from rich.text import Text

from harbor_cli.main import app
from harbor_cli.style import STYLE_CONFIG_OPTION
from harbor_cli.utils.commands import get_app_commands


def text_as_md(text: Text) -> str:
    if not text.spans:
        return text.plain
    for span in text.spans:
        if span.style != STYLE_CONFIG_OPTION:
            continue
        start, stop = span.start, span.end
        p = text.plain
        return p[:start] + f"`{p[start:stop]}`" + p[stop:]
    return text.plain


class OptionInfo(NamedTuple):
    params: tuple[str, ...]
    help: Text | None
    envvar: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "params": ", ".join(self.params),
            "help": text_as_md(self.help) if self.help else None,
            "envvar": self.envvar,
        }


if __name__ == "__main__":
    # TODO: find a more elegant way to retrieve the options from the main callback
    commands = get_app_commands(app)
    callback = app.registered_callback.callback

    options = []  # type: list[OptionInfo]
    for option in callback.__defaults__:
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
