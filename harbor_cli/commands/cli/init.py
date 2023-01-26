from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm
from rich.prompt import IntPrompt
from rich.prompt import Prompt

from ...app import app
from ...config import create_config
from ...config import DEFAULT_CONFIG_FILE
from ...config import HarborCLIConfig
from ...config import load_config
from ...config import save_config
from ...exceptions import ConfigError
from ...exceptions import OverwriteError
from ...logs import logger
from ...logs import LogLevel
from ...output.console import console
from ...output.console import success
from ...output.format import output_format_emoji
from ...output.format import output_format_repr
from ...output.format import OutputFormat
from ...output.formatting import path_link
from ...output.prompts import path_prompt
from ...output.prompts import str_prompt


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
        "--wizard",
        help="Run the configuration wizard after creating the config file.",
        is_flag=True,
    ),
) -> None:
    """Initialize Harbor CLI configuration file.

    Runs the configuration wizard by default unless otherwise specified.
    """

    logger.debug("Initializing Harbor CLI...")
    try:
        config_path = create_config(path, overwrite=overwrite)
    except OverwriteError:
        if not wizard:
            raise typer.Exit()
        # TODO: verify that this path is always correct
        p = path or DEFAULT_CONFIG_FILE
        console.print(
            f"WARNING: Config file already exists ({path_link(p)})", style="yellow"
        )
        wizard = Confirm.ask(
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

    config = load_config(config_path)
    assert config.config_file is not None

    console.print()
    console.rule(":sparkles: Harbor CLI Configuration Wizard :mage:")

    # We only ask the user to configure mandatory sections if the config
    # file existed prior to running wizard.
    # Otherwise, we force the user to configure Harbor settings, because
    # we can't do anything without them.
    if not conf_exists or Confirm.ask("\nConfigure harbor settings?", default=False):
        init_harbor_settings(config)
        console.print()

    # These categories are optional, and as such we always ask the user
    if Confirm.ask("Configure output settings?", default=False):
        init_output_settings(config)
        console.print()

    if Confirm.ask("Configure logging settings?", default=False):
        init_logging_settings(config)
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
    config.harbor.url = Prompt.ask(
        "Harbor API URL (e.g. https://harbor.example.com/api/v2.0)",
        default=hconf.url,
        show_default=True,
    )

    base_msg = "Authentication method [bold magenta](\[u]sername/password, \[b]asic auth, \[f]ile, \[s]kip)[/]"
    choices = ["u", "b", "f", "s"]

    auth_method = Prompt.ask(base_msg, choices=choices, default="s", show_choices=False)
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
        )
    elif auth_method == "b":
        hconf.basicauth = str_prompt(
            f"Harbor Base64 Basic Auth token",
            default=hconf.basicauth,
            password=True,
            empty_ok=False,
        )
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

    lconf.enabled = Confirm.ask(
        "Enable logging?", default=lconf.enabled, show_default=True
    )

    loglevel = Prompt.ask(
        "Logging level",
        choices=[lvl.value.lower() for lvl in LogLevel],
        default=lconf.level.value.lower(),  # use lower to match choices
        show_default=True,
    )
    lconf.level = LogLevel(loglevel.upper())


def init_output_settings(config: HarborCLIConfig) -> None:
    """Initialize output settings."""
    console.print("\n:desktop_computer: Output Configuration", style=TITLE_STYLE)

    oconf = config.output
    fmt_in = Prompt.ask(
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
        if Confirm.ask(
            f"\nConfigure {output_format_repr(fmt)} output settings?",
            default=False,
        ):
            conf_fmt(fmt)


def _init_output_json_settings(config: HarborCLIConfig) -> None:
    """Initialize JSON output settings."""
    _print_output_title(OutputFormat.JSON)

    oconf = config.output.JSON

    oconf.indent = IntPrompt.ask(
        "Indentation",
        default=oconf.indent,
        show_default=True,
    )

    oconf.sort_keys = Confirm.ask(
        "Sort keys",
        default=oconf.sort_keys,
        show_default=True,
    )


def _init_output_table_settings(config: HarborCLIConfig) -> None:
    """Initialize table output settings."""
    _print_output_title(OutputFormat.TABLE)

    oconf = config.output.table

    oconf.max_depth = IntPrompt.ask(
        "Max number of subtables [bold magenta](-1 or empty for unlimited)[/]",
        default=oconf.max_depth,
        show_default=True,
    )

    oconf.description = Confirm.ask(
        "Show descriptions",
        default=oconf.description,
        show_default=True,
    )

    oconf.compact = Confirm.ask(
        "Compact tables",
        default=oconf.compact,
        show_default=True,
    )


def _print_output_title(fmt: OutputFormat) -> None:
    fmt_repr = output_format_repr(fmt)
    emoji = output_format_emoji(fmt)
    console.print(
        f"\n:desktop_computer: {emoji} Output Configuration ({fmt_repr})",
        style=TITLE_STYLE,
    )
