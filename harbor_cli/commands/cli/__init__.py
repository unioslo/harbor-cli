"""Commands that are used to configure and interact with the CLI itself."""
from __future__ import annotations

import typer

from . import cache as cache
from . import cli_config as cli_config
from . import find as find
from . import init as init
from . import repl as repl
from . import sample_config as sample_config
from . import tui as tui

cli_commands: list[typer.Typer] = [cli_config.app, cache.app]
