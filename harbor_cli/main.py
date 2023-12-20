from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
import typer

from . import commands
from .__about__ import __version__
from .__about__ import APP_NAME
from .app import app
from .commands.cli.init import run_config_wizard
from .config import EnvVar
from .config import HarborCLIConfig
from .deprecation import Deprecated
from .deprecation import issue_deprecation_warnings
from .exceptions import ConfigError
from .exceptions import handle_exception
from .exceptions import HarborCLIError
from .format import OutputFormat
from .logs import disable_logging
from .logs import setup_logging
from .option import Option
from .output.console import error
from .output.console import exit_err
from .output.console import exit_ok
from .output.console import info
from .output.formatting.path import path_link
from .state import get_state
from .state import State


# Init subcommand groups here
for group in commands.ALL_GROUPS:
    app.add_typer(group)

_PRE_OVERRIDE_CONFIG = None  # type: HarborCLIConfig | None
"""A copy of the config before any REPL command overrides were applied."""


def _restore_config(state: State) -> None:
    """Restore the config to the state before any overrides were applied.

    Without this function, if you're in the REPL and run `--format json system info`,
    the next command will also use JSON format, even if --format wasn't specified,
    because the main callback would have overridden the output format in the config,
    and since the next command did not specify a format, it would fall back to the
    one found in the config, which would now be JSON.

    This function restores the original config to its state before any
    overrides were applied, so that they don't persist across commands.
    """
    global _PRE_OVERRIDE_CONFIG
    if _PRE_OVERRIDE_CONFIG is not None:
        state.config = _PRE_OVERRIDE_CONFIG
    if state.repl:
        _PRE_OVERRIDE_CONFIG = state.config.model_copy(deep=True)


CONFIG_EXEMPT_GROUPS = {"cli-config", "find", "sample-config", "version"}


def is_config_exempt(ctx: typer.Context):
    """Check if the command is exempt from requiring a config."""
    if not ctx.invoked_subcommand:  # no subcommand might require a config?
        return False
    if ctx.invoked_subcommand in CONFIG_EXEMPT_GROUPS:
        return True
    return False


def check_version_param(ctx: typer.Context, version: bool) -> None:
    """Check if --version was passed, and if so, print version and exit."""
    # Print version and exit if --version
    if version:
        exit_ok(f"{APP_NAME} version {__version__}")
    # Show error if no command and no version option
    if not version and not ctx.invoked_subcommand:
        raise click.UsageError("Missing command.")


# The callback defines global command options
@app.callback(no_args_is_help=True, invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    # Configuration options
    config_file: Optional[Path] = Option(
        None,
        "--config",
        "-c",
        help="Path to config file.",
        envvar=EnvVar.CONFIG,
    ),
    # Harbor options
    harbor_url: Optional[str] = Option(
        None,
        "--url",
        "-u",
        Deprecated("--harbor-url", replacement="--url"),
        help=f"Harbor API URL.",
        envvar=EnvVar.URL,
        config_override="harbor.url",
        rich_help_panel="Harbor",
    ),
    harbor_username: Optional[str] = Option(
        None,
        "--username",
        "-U",
        Deprecated("--harbor-username", replacement="--username"),
        help=f"Harbor username.",
        envvar=EnvVar.USERNAME,
        config_override="harbor.username",
        rich_help_panel="Harbor",
    ),
    harbor_secret: Optional[str] = Option(
        None,
        "--secret",
        "-S",
        Deprecated("--harbor-secret", replacement="--secret"),
        help=f"Harbor secret (password).",
        envvar=EnvVar.SECRET,
        config_override="harbor.secret",
        rich_help_panel="Harbor",
    ),
    harbor_basicauth: Optional[str] = Option(
        None,
        Deprecated("--basicauth"),
        Deprecated("-B"),
        help=f"Harbor basic access credentials (base64).",
        envvar=EnvVar.BASICAUTH,
        config_override="harbor.basicauth",
        rich_help_panel="Harbor",
    ),
    harbor_credentials_file: Optional[Path] = Option(
        None,
        "--credentials-file",
        "-F",
        help=f"Path to Harbor JSON credentials file.",
        envvar=EnvVar.CREDENTIALS_FILE,
        config_override="harbor.credentials_file",
        rich_help_panel="Harbor",
    ),
    harbor_validate: Optional[bool] = Option(
        None,
        "--validate/--no-validate",
        help=f"Validate Harbor API response data. Forces JSON output format if disabled.",
        envvar=EnvVar.HARBOR_VALIDATE_DATA,
        config_override="harbor.validate_data",
        rich_help_panel="Harbor",
    ),
    harbor_raw_mode: Optional[bool] = Option(
        None,
        "--raw/--no-raw",
        help=f"Return raw data from Harbor API. Overrides all output formatting options.",
        envvar=EnvVar.HARBOR_RAW_MODE,
        config_override="harbor.raw_mode",
        rich_help_panel="Harbor",
    ),
    harbor_verify_ssl: Optional[bool] = Option(
        None,
        "--verify-ssl/--no-verify-ssl",
        help=f"Verify SSL certificates when connecting to Harbor.",
        envvar=EnvVar.HARBOR_VERIFY_SSL,
        config_override="harbor.verify_ssl",
        rich_help_panel="Harbor",
    ),
    harbor_retry_enabled: Optional[bool] = Option(
        None,
        "--retry/--no-retry",
        help=f"Retry failed HTTP requests.",
        envvar=EnvVar.HARBOR_RETRY_ENABLED,
        config_override="harbor.retry.enabled",
        rich_help_panel="Harbor",
    ),
    harbor_retry_max_tries: Optional[int] = Option(
        None,
        "--retry-max-tries",
        help=f"Number of times to retry failed HTTP requests.",
        envvar=EnvVar.HARBOR_RETRY_MAX_TRIES,
        config_override="harbor.retry.max_tries",
        rich_help_panel="Harbor",
    ),
    harbor_retry_max_time: Optional[float] = Option(
        None,
        "--retry-max-time",
        help=f"Maximum number of seconds to retry failed HTTP requests.",
        envvar=EnvVar.HARBOR_RETRY_MAX_TIME,
        config_override="harbor.retry.max_time",
        rich_help_panel="Harbor",
    ),
    # Formatting
    show_description: Optional[bool] = Option(
        None,
        "--table-description/--no-table-description",
        help="Include field descriptions in tables.",
        envvar=EnvVar.TABLE_DESCRIPTION,
        config_override="output.table.description",
        rich_help_panel="Output",
    ),
    max_depth: Optional[int] = Option(
        None,
        "--table-max-depth",
        help="Maximum depth to print nested objects in tables.",
        envvar=EnvVar.TABLE_MAX_DEPTH,
        config_override="output.table.max_depth",
        rich_help_panel="Output",
    ),
    compact: Optional[bool] = Option(
        None,
        "--table-compact/--no-table-compact",
        help="Compact table output. Has no effect on other formats. ",
        envvar=EnvVar.TABLE_COMPACT,
        config_override="output.table.compact",
        rich_help_panel="Output",
    ),
    json_indent: Optional[int] = Option(
        None,
        "--json-indent",
        help="Indentation level for JSON output.",
        envvar=EnvVar.JSON_INDENT,
        config_override="output.json.indent",
        rich_help_panel="Output",
    ),
    json_sort_keys: Optional[bool] = Option(
        None,
        "--json-sort-keys/--no-json-sort-keys",
        help="Sort keys in JSON output.",
        envvar=EnvVar.JSON_SORT_KEYS,
        config_override="output.json.sort_keys",
        rich_help_panel="Output",
    ),
    # Output options
    output_format: Optional[OutputFormat] = Option(
        None,
        "--format",
        "-f",
        help=f"Specifies the output format to use.",
        envvar=EnvVar.OUTPUT_FORMAT,
        case_sensitive=False,
        config_override="output.format",
        rich_help_panel="Output",
    ),
    paging: Optional[bool] = Option(
        None,
        "--paging/--no-paging",
        help="Display output in a pager (less, etc.).",
        envvar=EnvVar.PAGING,
        config_override="output.paging",
        rich_help_panel="Output",
    ),
    pager: Optional[str] = Option(
        None,
        "--pager",
        help="Pager command to use. The default Rich pager will be used.",
        envvar=EnvVar.PAGER,
        config_override="output.pager",
        rich_help_panel="Output",
    ),
    # General options
    confirm_deletion: Optional[bool] = Option(
        None,
        "--confirm-deletion/--no-confirm-deletion",
        help="Confirm before deleting resources.",
        envvar=EnvVar.CONFIRM_DELETION,
        config_override="general.confirm_deletion",
        rich_help_panel="Confirmation & Alerts",
    ),
    confirm_enumeration: Optional[bool] = Option(
        None,
        "--confirm-enumeration/--no-confirm-enumeration",
        help="Confirm before enumerating all resources without a limit or query.",
        envvar=EnvVar.CONFIRM_ENUMERATION,
        config_override="general.confirm_enumeration",
        rich_help_panel="Confirmation & Alerts",
    ),
    warnings: Optional[bool] = Option(
        None,
        "--warnings/--no-warnings",
        help="Show/hide warnings.",
        envvar=EnvVar.WARNINGS,
        config_override="general.warnings",
        rich_help_panel="Confirmation & Alerts",
    ),
    # Cache options (DEPRECATED)
    cache_enabled: Optional[bool] = Option(
        None,
        Deprecated("--cache/--no-cache"),
        help="Enable caching of API responses.",
        config_override="cache.enabled",
        hidden=True,
    ),
    cache_ttl: Optional[int] = Option(
        None,
        Deprecated("--cache-ttl"),
        help="Cache TTL in seconds.",
        config_override="cache.ttl",
        hidden=True,
    ),
    # Output options that don't belong to the config file
    output_file: Optional[Path] = Option(
        None,
        "--output",
        "-o",
        help="Output file, by default None, which means output to stdout. If the file already exists, it will be overwritten.",
        rich_help_panel="Output",
    ),
    no_overwrite: bool = Option(
        False,
        "--no-overwrite",
        help="Do not overwrite the output file if it already exists.",
        rich_help_panel="Output",
    ),
    # stdout/stderr options
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
        rich_help_panel="Output",
    ),
    with_stdout: bool = Option(
        False,
        "--with-stdout",
        help="Output to stdout in addition to the specified output file, if any. Has no effect if no output file is specified.",
        rich_help_panel="Output",
    ),
    # Version
    version: bool = Option(
        None,
        "--version",
        help="Show application version and exit.",
    ),
) -> None:
    """
    Global configuration options.

    Most options passed in to this callback will override specific config
    file values. If an option is omitted, the config file value will be used.
    """
    check_version_param(ctx, version)
    issue_deprecation_warnings(ctx)

    # These commands don't require state management
    # and can be run without a config file or client.
    if is_config_exempt(ctx):
        # try to load the config file, but don't fail if it doesn't exist
        try_load_config(config_file, create=False)
        return

    # TODO: find a better way to do this
    # We don't want to run the rest of the callback if the user is asking
    # for help, so we check for the help option names and exit early if
    # any are present. The problem is that if the --help option is passed
    # to a subcommand, we can't access it through the ctx object here,
    # so we have to check the sys.argv list.
    if any(help_arg in sys.argv for help_arg in ctx.help_option_names):
        return

    # At this point we require an active configuation, be it from a file
    # loaded from disk or a default configuration.
    try_load_config(config_file, create=True)
    state = get_state()
    _restore_config(state)  # necessary for overrides to to reset in REPL

    # Set config overrides
    # Harbor
    if harbor_url is not None:
        state.config.harbor.url = harbor_url
    if harbor_username is not None:
        state.config.harbor.username = harbor_username
    if harbor_secret is not None:
        state.config.harbor.secret = harbor_secret  # type: ignore # Pydantic.SecretStr
        state.config.harbor.keyring = False
    if harbor_basicauth is not None:
        state.config.harbor.basicauth = harbor_basicauth  # type: ignore # Pydantic.SecretStr
    if harbor_credentials_file is not None:
        state.config.harbor.credentials_file = harbor_credentials_file
    if harbor_validate is not None:
        state.config.harbor.validate_data = harbor_validate
    if harbor_raw_mode is not None:
        state.config.harbor.raw_mode = harbor_raw_mode
    if harbor_verify_ssl is not None:
        state.config.harbor.verify_ssl = harbor_verify_ssl
    # Harbor retry
    if harbor_retry_enabled is not None:
        state.config.harbor.retry.enabled = harbor_retry_enabled
    if harbor_retry_max_tries is not None:
        state.config.harbor.retry.max_tries = harbor_retry_max_tries
    if harbor_retry_max_time is not None:
        state.config.harbor.retry.max_time = harbor_retry_max_time
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
    if warnings is not None:
        state.config.general.warnings = warnings

    # Set global options
    state.options.verbose = verbose
    state.options.output_file = output_file
    state.options.no_overwrite = no_overwrite
    state.options.with_stdout = with_stdout

    # Run configuration based on config file
    configure_from_config(state.config)


def configure_from_config(config: HarborCLIConfig) -> None:
    """Configure the program from a config file."""
    # TODO: Include more setup here
    if config.logging.enabled:
        setup_logging(config.logging)
    else:
        disable_logging()


def try_load_config(config_file: Optional[Path], create: bool = True) -> None:
    """Attempts to load the config given a config file path.
    Assigns the loaded config to the global state.

    Parameters
    ----------
    config_file : Optional[Path]
        The path to the config file.
    create : bool, optional
        Whether to create a new config file if one is not found, by default True
    """
    # Don't load the config if it's already loaded (e.g. in REPL)
    state = get_state()
    if not state.is_config_loaded:
        try:
            conf = HarborCLIConfig.from_file(config_file)
        except FileNotFoundError:
            if not create:
                return
            # Create a new config file and run wizard
            info("Config file not found. Creating new config file.")
            conf = HarborCLIConfig.from_file(config_file, create=create)
            if conf.config_file is None:
                exit_err("Unable to create config file.")
            info(f"Created config file: {path_link(conf.config_file)}")
            info("Running configuration wizard...")
            conf = run_config_wizard(conf.config_file)
        except ConfigError as e:
            error(f"Unable to load config: {str(e)}", exc_info=True)
            return

        state.config = conf


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except HarborCLIError as e:
        # exceptions of this type are expected, and if they're
        # not handled internally (i.e. other function calls exit_ok()),
        # we want to only display their message and exit with a
        # non-zero status code.
        exit_err(str(e))
    except Exception as e:
        handle_exception(e)
