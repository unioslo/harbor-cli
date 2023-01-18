"""Commands that are used to configure and interact with the CLI itself."""
from __future__ import annotations

import typer

from . import cli_config as cli_config
from . import init as init
from . import repl as repl
from . import sample_config as sample_config

# No subcommands for the CLI commands yet
cli_commands: list[typer.Typer] = [cli_config.app]
