from __future__ import annotations

from .api import api_commands
from .cli import cli_commands

groups = {
    "API": api_commands,
    "CLI": cli_commands,
}

# Patch help text for the different groups
for group_name, command_groups in groups.items():
    for command_group in command_groups:
        # command_group.info.help = f"[{group_name}] {command_group.info.help or ''}"
        pass

ALL_GROUPS = [command for group in groups.values() for command in group]
