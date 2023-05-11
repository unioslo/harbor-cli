from __future__ import annotations

from .api import api_commands
from .cli import cli_commands

groups = {
    "API": api_commands,
    "CLI": cli_commands,
}

ALL_GROUPS = [command for group in groups.values() for command in group]
