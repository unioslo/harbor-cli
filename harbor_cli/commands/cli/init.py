from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ...app import app
from ...config import create_config
from ...config import DEFAULT_CONFIG_FILE
from ...config import HarborCLIConfig
from ...config import save_config
from ...exceptions import ConfigError
from ...exceptions import OverwriteError
from ...format import output_format_emoji
from ...format import output_format_repr
from ...format import OutputFormat
from ...logs import logger
from ...logs import LogLevel
from ...output.console import console
from ...output.console import error
from ...output.console import exit
from ...output.console import exit_err
from ...output.console import success
from ...output.formatting import path_link
from ...output.prompts import bool_prompt
from ...output.prompts import int_prompt
from ...output.prompts import path_prompt
from ...output.prompts import str_prompt
from ...style import STYLE_COMMAND


TITLE_STYLE = "bold"  # Style for titles used by each config category
MAIN_TITLE_STYLE = "bold underline"  # Style for the main title


@app.command("init")
def init(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(
        None,
        help="Path to create config file.",
    ),
    overwrite: bool = typer.Option(
        False,
        help="Overwrite existing config file.",
        is_flag=True,
    ),
    wizard: bool = typer.Option(
        True,
        "--wizard/--no-wizard",
        help="Run the configuration wizard after creating the config file.",
        is_flag=True,
    ),
) -> None:
    """Initialize Harbor CLI configuration file.

    Runs the configuration wizard by default unless otherwise specified.
    """
    try:
        config_path = create_config(path, overwrite=overwrite)
    except OverwriteError:

        # TODO: verify that this path is always correct
        p = path or DEFAULT_CONFIG_FILE
        console.print(
            f"WARNING: Config file already exists ({path_link(p)})", style="yellow"
        )
        if not wizard:
            exit_err("Cannot proceed without overwriting config file.")

        wizard = bool_prompt(
            "Are you sure you want to run the configuration wizard?",
            default=False,
        )
        config_path = None
    else:
        logger.info(f"Created config file at {config_path}")

    if wizard:
        run_config_wizard(config_path)


def run_config_wizard(config_path: Optional[Path] = None) -> None:
    """Loads the config file, and runs the configuration wizard.

    Delegates to subroutines for each config category, that modify
    the loaded config object in-place."""
    conf_exists = config_path is None

    try:
        config = HarborCLIConfig.from_file(config_path)
    except Exception as e:
        error(f"Failed to load config: {e}")
        error(
            f"[white]Run [{STYLE_COMMAND}]harbor init --overwrite[/] to create a new config file.[/]"
        )
        exit(code=1)

    assert config.config_file is not None

    console.print()
    console.rule(":sparkles: Harbor CLI Configuration Wizard :mage:")

    # We only ask the user to configure mandatory sections if the config
    # file existed prior to running wizard.
    # Otherwise, we force the user to configure Harbor settings, because
    # we can't do anything without them.
    if not conf_exists or bool_prompt("\nConfigure harbor settings?", default=False):
        init_harbor_settings(config)
        console.print()

    # These categories are optional, and as such we always ask the user
    if bool_prompt("Configure output settings?", default=False):
        init_output_settings(config)
        console.print()

    if bool_prompt("Configure logging settings?", default=False):
        init_logging_settings(config)
        console.print()

    if bool_prompt("Configure REPL settings?", default=False):
        init_repl_settings(config)
        console.print()

    conf_path = config_path or config.config_file
    if not conf_path:
        raise ConfigError("Could not determine config file path.")
    save_config(config, conf_path)
    console.print("Configuration complete! :tada:")
    success(f"Saved config to {path_link(conf_path)}")


def init_harbor_settings(config: HarborCLIConfig) -> None:
    """Initialize Harbor settings."""
    console.print("\n:ship: Harbor Configuration", style=TITLE_STYLE)

    hconf = config.harbor
    config.harbor.url = str_prompt(
        "Harbor API URL (e.g. https://harbor.example.com/api/v2.0)",
        default=hconf.url,
        show_default=True,
    )

    base_msg = "Authentication method [bold magenta](\[u]sername/password, \[b]asic auth, \[f]ile, \[s]kip)[/]"
    choices = ["u", "b", "f", "s"]

    auth_method = str_prompt(base_msg, choices=choices, default="s", show_choices=False)
    if auth_method == "u":
        hconf.username = str_prompt(
            "Harbor username",
            default=hconf.username,
            empty_ok=False,
        )
        hconf.secret = str_prompt(
            "Harbor secret",
            default=hconf.secret,
            password=True,
            empty_ok=False,
        )  # type: ignore # pydantic.SecretStr
    elif auth_method == "b":
        hconf.basicauth = str_prompt(
            f"Harbor Base64 Basic Auth token",
            default=hconf.basicauth,
            password=True,
            empty_ok=False,
        )  # type: ignore # pydantic.SecretStr
    elif auth_method == "f":
        hconf.credentials_file = path_prompt(
            "Harbor credentials file",
            default=hconf.credentials_file,
            show_default=True,
            must_exist=True,
            exist_ok=True,
        )

    # Explain what will happen if no auth method is provided
    if not hconf.has_auth_method:
        console.print(
            ":warning: No authentication info provided. "
            "You will be prompted for username and password when required.",
            style="yellow",
        )


def init_logging_settings(config: HarborCLIConfig) -> None:
    """Initialize logging settings."""
    console.print("\n:mag: Logging Configuration", style=TITLE_STYLE)

    lconf = config.logging

    lconf.enabled = bool_prompt(
        "Enable logging?", default=lconf.enabled, show_default=True
    )

    loglevel = str_prompt(
        "Logging level",
        choices=[lvl.value.lower() for lvl in LogLevel],
        default=lconf.level.value.lower(),  # use lower to match choices
        show_default=True,
    )
    lconf.level = LogLevel(loglevel.upper())

    lconf.directory = path_prompt(
        "Log directory",
        default=lconf.directory,
        show_default=True,
        exist_ok=True,
        # NOTE: should we enforce that it exists?
    )

    lconf.filename = str_prompt(
        "Log filename",
        default=lconf.filename,
        show_default=True,
        empty_ok=False,
    )

    lconf.retention = int_prompt(
        "Log retention (days)",
        default=lconf.retention,
        show_default=True,
        min=1,
    )


def init_output_settings(config: HarborCLIConfig) -> None:
    """Initialize output settings."""
    console.print("\n:desktop_computer: Output Configuration", style=TITLE_STYLE)

    oconf = config.output

    # Output format configuration has numerous sub-options,
    # so we delegate to a separate function.
    _init_output_format(config)

    oconf.paging = bool_prompt(
        "Show output in pager? (requires 'less' or other pager to be installed and configured)",
        default=oconf.paging,
        show_default=True,
    )

    if oconf.paging:
        use_custom = bool_prompt(
            "Use custom pager command?", default=False, show_default=True
        )
        if use_custom:
            oconf.pager = str_prompt(
                "Pager command",
                default=oconf.pager,
                show_default=True,
                empty_ok=False,
            )


def _init_output_format(config: HarborCLIConfig) -> None:
    oconf = config.output
    fmt_in = str_prompt(
        "Default output format",
        choices=[f.value for f in OutputFormat],
        default=oconf.format.value,
    )
    oconf.format = OutputFormat(fmt_in)

    def conf_fmt(fmt: OutputFormat) -> None:
        if fmt == OutputFormat.JSON:
            _init_output_json_settings(config)
        elif fmt == OutputFormat.TABLE:
            _init_output_table_settings(config)
        else:
            logger.error(f"Unknown configuration format {fmt.value}")

    # Configure the chosen format first
    conf_fmt(oconf.format)

    # Optionally configure other formats afterwards
    formats = [f for f in OutputFormat if f != oconf.format]
    for fmt in formats:
        if bool_prompt(
            f"Configure {output_format_repr(fmt)} output settings?", default=False
        ):
            conf_fmt(fmt)


def _init_output_json_settings(config: HarborCLIConfig) -> None:
    """Initialize JSON output settings."""
    _print_output_title(OutputFormat.JSON)

    oconf = config.output.JSON

    oconf.indent = int_prompt(
        "Indentation",
        default=oconf.indent,
        show_default=True,
    )

    oconf.sort_keys = bool_prompt(
        "Sort keys",
        default=oconf.sort_keys,
        show_default=True,
    )


def _init_output_table_settings(config: HarborCLIConfig) -> None:
    """Initialize table output settings."""
    _print_output_title(OutputFormat.TABLE)

    oconf = config.output.table

    oconf.max_depth = int_prompt(
        "Max number of subtables [bold magenta](0 or omit for unlimited)[/]",
        default=oconf.max_depth,
        show_default=True,
    )

    oconf.description = bool_prompt(
        "Show descriptions",
        default=oconf.description,
        show_default=True,
    )

    oconf.compact = bool_prompt(
        "Compact tables",
        default=oconf.compact,
        show_default=True,
    )

    if bool_prompt("Configure table style?", default=False):
        _init_output_table_style_settings(config)


def _init_output_table_style_settings(config: HarborCLIConfig) -> None:
    """Initialize table style settings."""
    conf = config.output.table.style

    conf.title = str_prompt(
        "Title style",
        default=conf.title,
        empty_ok=True,
    )
    conf.header = str_prompt(
        "Header style",
        default=conf.header,
        empty_ok=True,
    )
    # TODO: ensure this is odd and even (not vice versa)
    odd_rows = str_prompt(
        "Row style (odd rows)",
        default=conf.rows[0] if conf.rows else "",
        empty_ok=True,
    )
    even_rows = str_prompt(
        "Row style (even rows)",
        default=conf.rows[1] if conf.rows else "",
        empty_ok=True,
    )
    conf.rows = (odd_rows, even_rows)

    conf.border = str_prompt(
        "Border style",
        default=conf.border,
        empty_ok=True,
    )

    conf.footer = str_prompt(
        "Footer style",
        default=conf.footer,
        empty_ok=True,
    )

    conf.caption = str_prompt(
        "Caption style",
        default=conf.caption,
        empty_ok=True,
    )

    conf.expand = bool_prompt(
        "Expand tables to terminal width",
        default=conf.expand,
    )

    conf.expand = bool_prompt(
        "Show table headers",
        default=conf.show_header,
    )


def init_repl_settings(config: HarborCLIConfig) -> None:
    conf = config.repl

    conf.history = bool_prompt(
        "Enable REPL history",
        default=conf.history,
    )

    if conf.history:
        conf.history_file = path_prompt(
            "REPL history file",
            default=conf.history_file,
            show_default=True,
            empty_ok=False,
        )


def _print_output_title(fmt: OutputFormat) -> None:
    fmt_repr = output_format_repr(fmt)
    emoji = output_format_emoji(fmt)
    console.print(
        f"\n:desktop_computer: {emoji} Output Configuration ({fmt_repr})",
        style=TITLE_STYLE,
    )
