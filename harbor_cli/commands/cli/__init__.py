"""Commands that are used to configure the CLI itself."""
from __future__ import annotations

import typer

from . import init as init
from . import sample_config as sample_config

# No subcommands for the CLI commands yet
cli_commands: list[typer.Typer] = []
