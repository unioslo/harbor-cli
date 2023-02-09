from __future__ import annotations

from typing import Any
from typing import cast
from typing import Optional

import typer
from typer.models import OptionInfo as _OptionInfo

from .style import help_config_override


class OptionInfo(_OptionInfo):
    config_override: Optional[str] = None
    _help_original: Optional[str] = None

    def __init__(self, *args, **kwargs) -> None:
        self.config_override = kwargs.pop("config_override", None)
        super().__init__(*args, **kwargs)

        # Not sure why mypy can't infer the type of help
        self.help = cast(Optional[str], self.help)  # type:ignore

        # Backup the original help text
        self._help_original = self.help
        if self.config_override:
            h = self.help or ""
            if h and not h.endswith(" "):
                h += " "
            self.help = h + help_config_override(self.config_override)


def Option(*args, config_override: str | None = None, **kwargs: Any) -> Any:
    kwargs.setdefault("show_envvar", False)  # disable by default
    kwargs.setdefault("show_default", False)  # disable by default

    # I'm sure this won't break in the future :)
    opt = typer.Option(*args, **kwargs)  # type: OptionInfo
    return OptionInfo(
        allow_dash=opt.allow_dash,
        allow_from_autoenv=opt.allow_from_autoenv,
        autocompletion=opt.autocompletion,
        callback=opt.callback,
        case_sensitive=opt.case_sensitive,
        clamp=opt.clamp,
        confirmation_prompt=opt.confirmation_prompt,
        count=opt.count,
        default=opt.default,
        envvar=opt.envvar,
        expose_value=opt.expose_value,
        flag_value=opt.flag_value,
        formats=opt.formats,
        help=opt.help,
        hidden=opt.hidden,
        hide_input=opt.hide_input,
        is_eager=opt.is_eager,
        is_flag=opt.is_flag,
        lazy=opt.lazy,
        max=opt.max,
        metavar=opt.metavar,
        min=opt.min,
        mode=opt.mode,
        param_decls=opt.param_decls,
        prompt=opt.prompt,
        prompt_required=opt.prompt_required,
        shell_complete=opt.shell_complete,
        show_choices=opt.show_choices,
        show_default=opt.show_default,
        show_envvar=opt.show_envvar,
        config_override=config_override,
    )
