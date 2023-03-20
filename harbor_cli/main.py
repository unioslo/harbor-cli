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
from .deprecation import check_deprecated_options
from .deprecation import Deprecated
from .exceptions import handle_exception
from .exceptions import HarborCLIError
from .format import OutputFormat
from .logs import disable_logging
from .logs import logger
from .logs import setup_logging
from .option import Option
from .output.console import exit_err
from .output.console import success
from .output.formatting.path import path_link
from .state import State
from .state import state

# Init subcommand groups here
for group in commands.ALL_GROUPS:
    app.add_typer(group)

_PRE_OVERRIDE_CONFIG = None  # type: HarborCLIConfig | None


def _restore_config(state: State) -> None:
    """Restore the config to the state before any overrides were applied.

    By default, if you're in the REPL and run `--format json system info`,
    the next command will also have use JSON format, even if not specified.
    This command restores the original config before the override was applied.
    """
    global _PRE_OVERRIDE_CONFIG
    if _PRE_OVERRIDE_CONFIG is not None:
        state.config = _PRE_OVERRIDE_CONFIG
    if state.repl:
        # NOTE: when we copy a model, fields that are marked as "exclude"
        # are _not_ copied, which is kind of insane? You would think
        # "exclude" only affects dumping dict/JSON, as the docstring implies,
        # but it also affects copying!
        _PRE_OVERRIDE_CONFIG = state.config.copy(
            update={"config_file": state.config.config_file}
        )


# The callback defines global command options
@app.callback(no_args_is_help=True)
def main_callback(
    ctx: typer.Context,
    # Configuration options
    config_file: Optional[Path] = Option(
        None,
        "--config",
        "-c",
        help="Path to config file.",
        envvar=env_var("config"),
    ),
    # Harbor options
    harbor_url: Optional[str] = Option(
        None,
        "--url",
        "-u",
        Deprecated("--harbor-url", replacement="--url"),
        help=f"Harbor API URL.",
        envvar=env_var("url"),
        config_override="harbor.url",
    ),
    harbor_username: Optional[str] = Option(
        None,
        "--username",
        "-U",
        Deprecated("--harbor-username", replacement="--username"),
        help=f"Harbor username.",
        envvar=env_var("username"),
        config_override="harbor.username",
    ),
    harbor_secret: Optional[str] = Option(
        None,
        "--secret",
        "-S",
        Deprecated("--harbor-secret", replacement="--secret"),
        help=f"Harbor secret (password).",
        envvar=env_var("secret"),
        config_override="harbor.secret",
    ),
    harbor_basicauth: Optional[str] = Option(
        None,
        "--basicauth",
        "-B",
        help=f"Harbor basic access credentials (base64).",
        envvar=env_var("basicauth"),
        config_override="harbor.basicauth",
    ),
    harbor_credentials_file: Optional[Path] = Option(
        None,
        "--credentials-file",
        "-F",
        help=f"Path to Harbor JSON credentials file.",
        envvar=env_var("credentials_file"),
        config_override="harbor.credentials_file",
    ),
    harbor_validate: Optional[bool] = Option(
        None,
        "--harbor-validate/--no-harbor-validate",
        help=f"Validate Harbor API response data. Forces JSON output format.",
        envvar=env_var("harbor_validate_data"),
        config_override="harbor.validate_data",
    ),
    harbor_raw_mode: Optional[bool] = Option(
        None,
        "--harbor-raw/--no-harbor-raw",
        help=f"Return raw data from Harbor API. Ignores output format and formatting options.",
        envvar=env_var("harbor_raw_mode"),
        config_override="harbor.raw_mode",
    ),
    # Formatting
    show_description: Optional[bool] = Option(
        None,
        "--table-description/--no-table-description",
        help="Include field descriptions in tables.",
        envvar=env_var("table_description"),
        config_override="output.table.description",
    ),
    max_depth: Optional[int] = Option(
        None,
        "--table-max-depth",
        help="Maximum depth to print nested objects in tables.",
        envvar=env_var("table_max_depth"),
        config_override="output.table.max_depth",
    ),
    compact: Optional[bool] = Option(
        None,
        "--table-compact/--no-table-compact",
        help="Compact table output. Has no effect on other formats. ",
        envvar=env_var("table_compact"),
        config_override="output.table.compact",
    ),
    json_indent: Optional[int] = Option(
        None,
        "--json-indent",
        help="Indentation level for JSON output.",
        envvar=env_var("json_indent"),
        config_override="output.json.indent",
    ),
    json_sort_keys: Optional[bool] = Option(
        None,
        "--json-sort-keys/--no-json-sort-keys",
        help="Sort keys in JSON output.",
        envvar=env_var("json_sort_keys"),
        config_override="output.json.sort_keys",
    ),
    # Output options
    output_format: Optional[OutputFormat] = Option(
        None,
        "--format",
        "-f",
        help=f"Specifies the output format to use.",
        envvar=env_var("output_format"),
        case_sensitive=False,
        config_override="output.format",
    ),
    paging: Optional[bool] = Option(
        None,
        "--paging/--no-paging",
        help="Display output in a pager (less, etc.).",
        envvar=env_var("paging"),
        config_override="output.paging",
    ),
    pager: Optional[str] = Option(
        None,
        "--pager",
        help="Pager command to use. The default Rich pager will be used.",
        envvar=env_var("pager"),
        config_override="output.pager",
    ),
    # General options
    confirm_deletion: Optional[bool] = Option(
        None,
        "--confirm-deletion/--no-confirm-deletion",
        help="Confirm before deleting resources..",
        envvar=env_var("confirm_deletion"),
        config_override="general.confirm_deletion",
    ),
    confirm_enumeration: Optional[bool] = Option(
        None,
        "--confirm-enumeration/--no-confirm-enumeration",
        help="Confirm before enumerating all resources without a limit or query.",
        envvar=env_var("confirm_enumeration"),
        config_override="general.confirm_enumeration",
    ),
    # Output options that don't belong to the config file
    output_file: Optional[Path] = Option(
        None,
        "--output",
        "-o",
        help="Output file, by default None, which means output to stdout. If the file already exists, it will be overwritten.",
    ),
    no_overwrite: bool = Option(
        False,
        "--no-overwrite",
        help="Do not overwrite the output file if it already exists.",
    ),
    # stdout/stderr options
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose output."),
    with_stdout: bool = Option(
        False,
        "--with-stdout",
        help="Output to stdout in addition to the specified output file, if any. Has no effect if no output file is specified.",
    ),
) -> None:
    """
    Configuration options that affect all commands.
    """
    check_deprecated_options(ctx)

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

    _restore_config(state)  # necessary for overrides to to reset in REPL

    # Set config overrides
    # Harbor
    if harbor_url is not None:
        state.config.harbor.url = harbor_url
    if harbor_username is not None:
        state.config.harbor.username = harbor_username
    if harbor_secret is not None:
        state.config.harbor.secret = harbor_secret  # type: ignore
    if harbor_basicauth is not None:
        state.config.harbor.basicauth = harbor_basicauth  # type: ignore
    if harbor_credentials_file is not None:
        state.config.harbor.credentials_file = harbor_credentials_file
    if harbor_validate is not None:
        state.config.harbor.validate_data = harbor_validate
    if harbor_raw_mode is not None:
        state.config.harbor.raw_mode = harbor_raw_mode
    # Output
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
    if paging is not None:
        state.config.output.paging = paging
    if pager is not None:
        state.config.output.pager = pager
    # General
    if confirm_enumeration is not None:
        state.config.general.confirm_enumeration = confirm_enumeration
    if confirm_deletion is not None:
        state.config.general.confirm_deletion = confirm_deletion

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
        setup_logging(config.logging)
    else:
        disable_logging()

    # Force JSON output format if validation==False and raw_mode==True
    if not config.harbor.validate_data and not config.harbor.raw_mode:
        logger.warning(
            "Data validation is disabled. Forcing JSON output format. "
            "Change output mode to JSON in the config or via CLI options to suppress this warning."
        )
        config.output.format = OutputFormat.JSON


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
