from __future__ import annotations

from typing import Callable
from typing import Dict
from typing import Literal

from harborapi.models.scanner import Severity
from strenum import StrEnum


def blue(message: str) -> str:
    return f"[blue]{message}[/]"


def cyan(message: str) -> str:
    return f"[cyan]{message}[/]"


def green(message: str) -> str:
    return f"[green]{message}[/]"


def magenta(message: str) -> str:
    return f"[magenta]{message}[/]"


def red(message: str) -> str:
    return f"[red]{message}[/]"


def yellow(message: str) -> str:
    return f"[yellow]{message}[/]"


def bold(message: str) -> str:
    return f"[bold]{message}[/]"


Color = Literal["blue", "cyan", "green", "magenta", "red", "yellow", "bold"]
ColorFunc = Callable[[str], str]
COLOR_FUNCTIONS: Dict[Color, ColorFunc] = {
    "blue": blue,
    "cyan": cyan,
    "green": green,
    "magenta": magenta,
    "red": red,
    "yellow": yellow,
    "bold": bold,
}


def get_color_func(color: Color) -> ColorFunc:
    return COLOR_FUNCTIONS[color]


class HealthColor(StrEnum):
    HEALTHY = "green"
    UNHEALTHY = "red"

    @classmethod
    def from_health(cls, health: str | None) -> str:
        if health == "healthy":
            return HealthColor.HEALTHY
        else:
            return HealthColor.UNHEALTHY


class SeverityColor(StrEnum):
    CRITICAL = "dark_red"
    HIGH = "red"
    MEDIUM = "orange3"
    LOW = "green"
    NEGLIGIBLE = "blue"
    NONE = "white"
    UNKNOWN = "white"

    @classmethod
    def from_severity(cls, severity: str | Severity) -> str:
        """Return the color for the given severity level."""
        if isinstance(severity, Severity):
            severity = severity.value
        try:
            color = getattr(cls, severity.upper())
            if isinstance(color, SeverityColor):
                return color
            raise ValueError(f"Invalid severity: {severity}")
        except (AttributeError, ValueError):
            return SeverityColor.UNKNOWN

    @classmethod
    def as_markup(cls, severity: str | Severity) -> str:
        """Return the given severity as a Rich markup-formatted string."""
        color = cls.from_severity(severity)
        return f"[{color}]{severity}[/]"
