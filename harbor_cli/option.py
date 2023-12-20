from __future__ import annotations

from typing import Any
from typing import cast
from typing import Optional

from typer.models import OptionInfo as _OptionInfo

from .style import render_config_option


def help_config_override(option: str) -> str:
    """Render a help string for a configuration file option/key/entry."""
    return f"Overrides config option {render_config_option(option)}."


class OptionInfo(_OptionInfo):
    config_override: Optional[str] = None
    _help_original: Optional[str] = None

    def __init__(self, *args, **kwargs) -> None:
        self.config_override = kwargs.pop("config_override", None)
        super().__init__(*args, **kwargs)

        # Not sure why mypy can't infer the type of help
        self.help = cast(Optional[str], self.help)  # type: ignore

        # Backup the original help text
        self._help_original = self.help
        if self.config_override:
            h = self.help or ""
            if h and not h.endswith(" "):
                h += " "
            self.help = f"{h}{help_config_override(self.config_override)}"


def Option(
    default: Optional[Any] = ...,
    *param_decls: str,
    config_override: str | None = None,
    **kwargs: Any,
) -> Any:
    """A wrapper around typer.Option that creates a custom `OptionInfo` class
    that also contains information about the configuration file entry that
    the option overrides.

    Modifies the help text to include the config override info.

    Parameters
    ----------
    default : Optional[Any], optional
        The default value of the option
        The names of the option
    config_override : str, optional
        Dot-separated path to the config file entry that the option overrides.
        E.g. `--harbor-url` overrides `harbor.url` in the config file.
    **kwargs : Any
        Additional keyword arguments to pass to `typer.Option`.
        Takes all the same kwargs as `typer.Option`.
    """
    kwargs.setdefault("show_envvar", False)  # disable by default
    kwargs.setdefault("show_default", False)  # disable by default

    return OptionInfo(
        default=default,
        param_decls=param_decls,
        **kwargs,
        config_override=config_override,
    )
