# Rich markup styles for the CLI
from __future__ import annotations

STYLE_CONFIG_OPTION = "italic yellow"
"""Style used to signify a configuration file option/key/entry."""

STYLE_CLI_OPTION = "green"
"""Style used to signify a CLI option, e.g. --verbose."""

STYLE_CLI_VALUE = "bold magenta"
"""Style used in command docstrings to signify a CLI value e.g. 'FILE'."""

STYLE_TABLE_HEADER = "bold green"
STYLE_COMMAND = "bold italic green"
STYLE_WARNING = "yellow"


def render_warning(msg: str) -> str:
    return f"[{STYLE_WARNING}]WARNING: {msg}[/]"


def render_config_option(option: str) -> str:
    """Render a configuration file option/key/entry."""
    return f"[{STYLE_CONFIG_OPTION}]{option}[/]"


def render_cli_option(option: str) -> str:
    """Render a CLI option."""
    return f"[{STYLE_CLI_OPTION}]{option}[/]"


def render_cli_value(value: str) -> str:
    """Render a CLI value."""
    return f"[{STYLE_CLI_VALUE}]{value}[/]"


def help_config_override(option: str) -> str:
    """Render a help string for a configuration file option/key/entry."""
    return f"Overrides config option {render_config_option(option)}."
