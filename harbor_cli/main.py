from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from . import commands
from . import harbor
from .app import app
from .config import env_var
from .config import HarborCLIConfig
from .deprecation import check_deprecated_option
from .exceptions import handle_exception
from .exceptions import HarborCLIError
from .format import OutputFormat
from .logs import disable_logging
from .logs import logger
from .logs import setup_logging
from .output.console import exit_err
from .output.console import success
from .output.formatting.path import path_link
from .state import state
from .style import help_config_override

# Init subcommand groups here
for group in commands.ALL_GROUPS:
    app.add_typer(group)

# The callback defines global command options
@app.callback(no_args_is_help=True)
def main_callback(
    ctx: typer.Context,
    # Configuration options
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file.",
        envvar=env_var("config"),
    ),
    # Harbor options
    harbor_url: Optional[str] = typer.Option(
        None,
        "--harbor-url",
        "-u",
        help=f"Harbor API URL. {help_config_override('harbor.url')}",
        envvar=env_var("url"),
    ),
    harbor_username: Optional[str] = typer.Option(
        None,
        "--harbor-username",
        "-U",
        help=f"Harbor username. {help_config_override('harbor.username')}",
        envvar=env_var("username"),
    ),
    harbor_secret: Optional[str] = typer.Option(
        None,
        "--harbor-secret",
        "-S",
        help=f"Harbor secret (password). {help_config_override('harbor.secret')}",
        envvar=env_var("secret"),
    ),
    harbor_basicauth: Optional[str] = typer.Option(
        None,
        "--basicauth",
        "-B",
        help=f"Harbor basic access credentials (base64). {help_config_override('harbor.basicauth')}",
        envvar=env_var("basicauth"),
    ),
    harbor_credentials_file: Optional[Path] = typer.Option(
        None,
        "--credentials-file",
        "-F",
        help=f"Path to Harbor JSON credentials file. {help_config_override('harbor.credentials_file')}",
        envvar=env_var("credentials_file"),
    ),
    # Formatting
    show_description: Optional[bool] = typer.Option(
        None,
        "--table-description/--no-table-description",
        help=(
            "Include field descriptions in tables. "
            f"{help_config_override('output.table.description')}"
        ),
        envvar=env_var("table_description"),
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--table-max-depth",
        help=(
            "Maximum depth to print nested objects in tables. "
            f"{help_config_override('output.table.max_depth')}"
        ),
        envvar=env_var("table_max_depth"),
    ),
    compact: Optional[bool] = typer.Option(
        None,
        "--table-compact/--no-table-compact",
        help=(
            "Compact table output. Has no effect on other formats. "
            f"{help_config_override('output.table.compact')}"
        ),
        envvar=env_var("table_compact"),
    ),
    json_indent: Optional[int] = typer.Option(
        None,
        "--json-indent",
        help=f"Indentation level for JSON output. {help_config_override('output.json.indent')}",
        envvar=env_var("json_indent"),
    ),
    json_sort_keys: Optional[bool] = typer.Option(
        None,
        "--json-sort-keys/--no-json-sort-keys",
        help=f"Sort keys in JSON output. {help_config_override('output.json.sort_keys')}",
        envvar=env_var("json_sort_keys"),
    ),
    # Output options
    output_format: Optional[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help=f"Specifies the output format to use. {help_config_override('output.format')}",
        envvar=env_var("output_format"),
        case_sensitive=False,
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
    check_deprecated_option(ctx)

    # These commands don't require state management
    # and can be run without a config file or client.
    if ctx.invoked_subcommand in ["sample-config", "init", "find"]:
        return

    # TODO: find a better way to do this
    # We don't want to run the rest of the callback if the user is asking
    # for help, so we check for the help option names and exit early if
    # any are present. The problem is that if the --help option is passed
    # to a subcommand, we can't access it through the ctx object here,
    # so we have to check the sys.argv list.
    if any(help_arg in sys.argv for help_arg in ctx.help_option_names):
        return

    # if we're in the REPL, we don't want to load config again
    if not state.config_loaded:
        try:
            conf = HarborCLIConfig.from_file(config_file)
        except FileNotFoundError:
            # Create a new config file, but don't run wizard
            logger.info("Config file not found. Creating new config file.")
            conf = HarborCLIConfig.from_file(config_file, create=True)
            if conf.config_file is None:
                exit_err("Unable to create config file.")
            success(f"Created config file at {path_link(conf.config_file)}")
            logger.info("Proceeding with default configuration.")
            logger.info("Run 'harbor init' to configure Harbor CLI. ")
        state.add_config(conf)

    # Set config overrides
    if compact is not None:
        state.config.output.table.compact = compact
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

    # Instantiate the client
    client = harbor.setup_client(state.config)
    state.add_client(client)

    # Run configuration based on config file
    configure_from_config(state.config)


def configure_from_config(config: HarborCLIConfig) -> None:
    """Configure the program from a config file."""
    # TODO: Include more setup here
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
    except Exception as e:
        handle_exception(e)
