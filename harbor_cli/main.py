from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from . import commands
from . import harbor
from .app import app
from .config import HarborCLIConfig
from .exceptions import exit_err
from .exceptions import HarborCLIError
from .logs import disable_logging
from .logs import setup_logging
from .output.format import OutputFormat
from .state import state

# Init subcommand groups here
for group in commands.ALL_GROUPS:
    app.add_typer(group)

# The callback defines global command options
@app.callback(no_args_is_help=True)
def main_callback(
    ctx: typer.Context,
    # Configuration options
    config_file: Optional[Path] = typer.Option(
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
    show_description: Optional[bool] = typer.Option(
        False,
        "--table-description",
        help="Include field descriptions in tables. Only affects tables.",
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--table-max-depth",
        help="Maximum depth to print nested objects. Only affects tables." "",
    ),
    json_indent: Optional[int] = typer.Option(
        None,
        "--json-indent",
        help="Indentation level for JSON output. Affects JSON and JSON schema.",
    ),
    json_sort_keys: Optional[bool] = typer.Option(
        None,
        "--json-sort-keys",
        help="Sort keys in JSON output. Affects JSON and JSON schema.",
    ),
    # Output options
    output_format: OutputFormat = typer.Option(
        OutputFormat.TABLE.value,
        "--format",
        "-f",
        help=f"Output format.",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file, by default None, which means output to stdout. If the file already exists, it will be overwritten.",
    ),
    no_overwrite: bool = typer.Option(
        False,
        "--no-overwrite",
        help="Do not overwrite the output file if it already exists.",
    ),
    # stdout/stderr options
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
    with_stdout: bool = typer.Option(
        False,
        "--with-stdout",
        help="Output to stdout in addition to the specified output file, if any. Has no effect if no output file is specified.",
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
    # We don't want to run the rest of the callback if the useris asking
    # for help, so we check for the help option names and exit early if
    # any are present. The problem is that if the --help option is passed
    # to a subcommand, we can't access it through the ctx object here,
    # so we have to check the sys.argv list.
    if any(help_arg in sys.argv for help_arg in ctx.help_option_names):
        return

    if config_file:
        # If a config file is specified, it needs to exist
        state.config = HarborCLIConfig.from_file(config_file)
    else:
        # Support creating config file if no path is specified,
        # and the default config file doesn't exist.
        state.config = HarborCLIConfig.from_file(create=True)

    # Set config overrides
    if show_description is not None:
        state.config.output.table.description = show_description
    if max_depth is not None:
        state.config.output.table.max_depth = max_depth
    if json_indent is not None:
        state.config.output.JSON.indent = json_indent
    if json_sort_keys is not None:
        state.config.output.JSON.sort_keys = json_sort_keys
    if output_format is not None:
        state.config.output.format = output_format

    # Set global options
    state.options.verbose = verbose
    state.options.output_file = output_file
    state.options.no_overwrite = no_overwrite
    state.options.with_stdout = with_stdout

    state.client = harbor.get_client(state.config)
    # TODO: run configure_from_config and expand it to include all options


def configure_from_config(config: HarborCLIConfig) -> None:
    """Configure the program from a config file."""
    if config.logging.enabled:
        setup_logging(config.logging.level)
    else:
        disable_logging()


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except HarborCLIError as e:
        # exceptions of this type are expected, and if they're
        # not handled internally (i.e. other function calls exit()),
        # we want to only display their message and exit with a
        # non-zero status code.
        exit_err(str(e))
