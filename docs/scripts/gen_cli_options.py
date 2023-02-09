from __future__ import annotations

from typing import NamedTuple
from typing import Sequence

import yaml  # type: ignore
from common import DATA_PATH

from harbor_cli.deprecation import Deprecated
from harbor_cli.main import app
from harbor_cli.utils.commands import get_app_callback_options


def maybe_list_to_str(text: str | list[str] | None) -> str | None:
    if isinstance(text, str) or text is None:
        return text
    return ", ".join(text) or None


# name it OptInfo to avoid confusion with typer.models.OptionInfo
class OptInfo(NamedTuple):
    params: Sequence[str]
    help: str | None
    envvar: str | list[str] | None
    config_value: str | None

    @property
    def fragment(self) -> str | None:
        if self.config_value is None:
            return None
        return self.config_value.replace(".", "")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "params": ", ".join(f"`{p}`" for p in self.params),
            "help": self.help or "",
            "envvar": maybe_list_to_str(self.envvar),
            "config_value": self.config_value,
            "fragment": self.fragment,
        }


if __name__ == "__main__":
    options = []  # type: list[OptInfo]
    for option in get_app_callback_options(app):
        if not option.param_decls:
            continue
        conf_value = None
        if hasattr(option, "config_override"):
            conf_value = option.config_override
        h = option._help_original if hasattr(option, "_help_original") else option.help
        o = OptInfo(
            params=[p for p in option.param_decls if not isinstance(p, Deprecated)],
            help=h,
            envvar=option.envvar,
            config_value=conf_value,
        )
        options.append(o)

    to_dump = [o.to_dict() for o in options]

    with open(DATA_PATH / "options.yaml", "w") as f:
        yaml.dump(to_dump, f, sort_keys=False)
