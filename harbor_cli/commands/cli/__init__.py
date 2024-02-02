"""Commands that are used to configure and interact with the CLI itself."""
from __future__ import annotations

import copy

import typer

from . import cache as cache
from . import find as find
from . import init as init
from . import repl as repl
from . import sample_config as sample_config
from . import self as self
from . import tui as tui
from harbor_cli.style.style import render_cli_command

# Compatibility for deprecated `cli-config` command
# Which now lives on as `self config`
_cli_config_cmd = copy.deepcopy(self.config_cmd)
_cli_config_cmd.info.name = "cli-config"
_cli_config_cmd.info.deprecated = True
_cli_config_cmd.info.hidden = True
_cli_config_cmd.info.help = (
    str(_cli_config_cmd.info.help)
    + f" Use {render_cli_command('self config')} instead."
)

cli_commands: list[typer.Typer] = [self.app, _cli_config_cmd, cache.app]
