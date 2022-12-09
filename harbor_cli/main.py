from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from . import commands
from . import harbor
from .app import app
from .config import HarborCLIConfig
from .logs import disable_logging
from .logs import setup_logging
from .output.format import OutputFormat
from .state import state

# Init subcommand groups here
for group in commands.ALL_GROUPS:
    app.add_typer(group)

# The callback defines global command options
@app.callback(no_args_is_help=True)
def main(
    ctx: typer.Context,
    # Configuration options
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to config file."
    ),
    # Harbor options
    harbor_url: Optional[str] = typer.Option(None, "--url", "-u", help="Harbor URL."),
    harbor_username: Optional[str] = typer.Option(
        None, "--username", "-U", help="Harbor username."
    ),
    harbor_secret: Optional[str] = typer.Option(None),
    harbor_credentials: Optional[str] = typer.Option(
        None, "--credentials", "-C", help="Harbor basic access credentials (base64)."
    ),
    harbor_credentials_file: Optional[Path] = typer.Option(
        None, "--credentials-file", "-F", help="Harbor basic access credentials file."
    ),
    # Formatting
    output_format: OutputFormat = typer.Option(
        OutputFormat.TABLE.value,
        "--format",
        "-f",
        help=f"Output format.",
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file."
    ),
) -> None:
    """
    Configuration options that affect all commands.
    """
    setup_logging()

    # These commands don't require state management
    # and can be run without a config file or client.
    if ctx.invoked_subcommand in ["sample-config", "init"]:
        return

    # TODO: find a better way to do this
    if any(help_arg in sys.argv for help_arg in ctx.help_option_names):
        return

    if verbose:
        state.verbose = True

    if config:
        # If a config file is specified, it needs to exist
        state.config = HarborCLIConfig.from_file(config)
    else:
        # Support creating config file if no path is specified,
        # and the default config file doesn't exist.
        state.config = HarborCLIConfig.from_file(create=True)

    state.client = harbor.get_client(state.config)


def configure_from_config(config: HarborCLIConfig) -> None:
    """Configure the program from a config file."""
    if config.logging.enabled:
        setup_logging(config.logging.level)
    else:
        disable_logging()
