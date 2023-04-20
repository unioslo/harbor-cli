# Rich markup styles for the CLI
from __future__ import annotations

from typing import Any

from harborapi.models.scanner import Severity

STYLE_CONFIG_OPTION = "italic yellow"
"""Used to signify a configuration file option/key/entry."""

STYLE_CLI_OPTION = "green"
"""Used to signify a CLI option, e.g. --verbose."""

STYLE_CLI_VALUE = "bold magenta"
"""Used to signify a CLI value e.g. 'FILE'."""

STYLE_CLI_COMMAND = "bold green"
"""Used to signify a CLI command e.g. 'artifact get'."""

STYLE_TABLE_HEADER = "bold green"
STYLE_COMMAND = "bold italic green"
STYLE_WARNING = "yellow"


EMOJI_YES = ":white_check_mark:"
EMOJI_NO = ":cross_mark:"


# Colors
# Colors should be used to colorize output and help define styles,
# but they should not contain any formatting (e.g. bold, italic, `x` on `y`, etc.)
COLOR_CVE_CRITICAL = "dark_red"
COLOR_CVE_HIGH = "red"
COLOR_CVE_MEDIUM = "orange3"
COLOR_CVE_LOW = "green"
COLOR_CVE_NEGLIGIBLE = "blue"
COLOR_CVE_UNKNOWN = "white"
COLOR_HEALTH_HEALTHY = "green"
COLOR_HEALTH_UNHEALTHY = "red"


STYLE_CVE_SEVERITY = {
    "critical": COLOR_CVE_CRITICAL,
    "high": COLOR_CVE_HIGH,
    "medium": COLOR_CVE_MEDIUM,
    "low": COLOR_CVE_LOW,
    "negligible": COLOR_CVE_NEGLIGIBLE,
    "unknown": COLOR_CVE_UNKNOWN,
}


def get_severity_style(severity: str | Severity) -> str:
    if isinstance(severity, Severity):
        severity = severity.value.lower()
    return STYLE_CVE_SEVERITY.get(severity, "white")


def render_warning(msg: str) -> str:
    return f"[{STYLE_WARNING}]WARNING: {msg}[/]"


def render_config_option(option: str) -> str:
    """Render a configuration file option/key/entry."""
    return f"[{STYLE_CONFIG_OPTION}]{option}[/]"


def render_cli_option(option: str) -> str:
    """Render a CLI option."""
    return f"[{STYLE_CLI_OPTION}]{option}[/]"


def render_cli_value(value: Any) -> str:
    """Render a CLI value/argument."""
    return f"[{STYLE_CLI_VALUE}]{value!r}[/]"


def render_cli_command(value: str) -> str:
    """Render a CLI command."""
    return f"[{STYLE_CLI_COMMAND}]{value}[/]"


def help_config_override(option: str) -> str:
    """Render a help string for a configuration file option/key/entry."""
    return f"Overrides config option {render_config_option(option)}."


def get_health_color(health: str | None) -> str:
    if health == "healthy":
        return COLOR_HEALTH_HEALTHY
    else:  # TODO: find all health states
        return COLOR_HEALTH_UNHEALTHY
