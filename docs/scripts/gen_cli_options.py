from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple
from typing import Sequence

import yaml  # type: ignore

from harbor_cli.deprecation import Deprecated
from harbor_cli.main import app
from harbor_cli.utils.commands import get_app_callback_options

sys.path.append(Path(__file__).parent.as_posix())
from common import DATA_DIR  # noqa


def maybe_list_to_str(text: str | list[str] | None) -> str | None:
    # The envvars might actually be instances of `harbor_cli.config.EnvVar`,
    # which the YAML writer does not convert to strings. Hence `str(...)`
    if text is None:
        return None
    if isinstance(text, str):
        return str(text)
    return ", ".join([str(t) for t in text])


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


def main() -> None:
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

    with open(DATA_DIR / "options.yaml", "w") as f:
        yaml.dump(to_dump, f, sort_keys=False)


if __name__ == "__main__":
    main()
