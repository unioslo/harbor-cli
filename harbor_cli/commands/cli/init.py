from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm
from rich.prompt import IntPrompt
from rich.prompt import Prompt

from ...app import app
from ...config import create_config
from ...config import HarborCLIConfig
from ...config import load_config
from ...config import save_config
from ...exceptions import ConfigError
from ...exceptions import OverwriteError
from ...logs import logger
from ...logs import LogLevel
from ...output.console import console
from ...output.format import output_format_repr
from ...output.format import OutputFormat
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
    no_wizard: bool = typer.Option(
        False,
        help="Do not run the configuration wizard after creating the config file.",
        is_flag=True,
    ),
) -> None:
    """Initialize Harbor CLI."""
    # Invert flag (easier to reason about)
    run_wizard = not no_wizard

    logger.debug("Initializing Harbor CLI...")
    try:
        config_path = create_config(path, overwrite=overwrite)
    except OverwriteError:
        if not run_wizard:
            raise typer.Exit()
        run_wizard = Confirm.ask(
            "Config file already exists. Run configuration wizard?",
            default=False,
        )
        config_path = None
    else:
        logger.info(f"Created config file at {config_path}")

    if run_wizard:
        run_config_wizard(config_path)


def run_config_wizard(config_path: Optional[Path] = None) -> None:
    """Loads the config file, and runs the configuration wizard.

    Delegates to subroutines for each config category, that modify
    the loaded config object in-place."""
    conf_exists = config_path is None

    config = load_config(config_path)
    assert config.config_file is not None

    console.print()
    console.rule("Harbor CLI Configuration Wizard")

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
    logger.info(f"Saved config to {conf_path}")
    console.rule("Configuration complete!")


def init_harbor_settings(config: HarborCLIConfig) -> None:
    """Initialize Harbor settings."""
    console.print("\nHarbor Configuration", style=TITLE_STYLE)

    hconf = config.harbor
    config.harbor.url = Prompt.ask(
        "Harbor URL",
        default=hconf.url,
        show_default=True,
    )

    auth_scheme = Prompt.ask(
        "Authentication scheme: \[u]sername/password, \[t]oken or \[f]ile",
        choices=["u", "t", "f"],
    )
    if auth_scheme == "u":
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
    elif auth_scheme == "t":
        hconf.credentials_base64 = str_prompt(
            f"Harbor base64 credentials",
            default=hconf.credentials_base64,
            password=True,
            empty_ok=False,
        )
    elif auth_scheme == "f":
        hconf.credentials_file = path_prompt(
            "Harbor credentials file",
            default=hconf.credentials_file,
            show_default=True,
            must_exist=True,
            exist_ok=True,
        )


def init_logging_settings(config: HarborCLIConfig) -> None:
    """Initialize logging settings."""
    console.print("\nLogging Configuration", style=TITLE_STYLE)

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
    console.print("\nOutput Configuration", style=TITLE_STYLE)

    oconf = config.output
    fmt_in = Prompt.ask(
        "Output format",
        choices=[f.value for f in OutputFormat],
        default=oconf.format.value,
    )
    oconf.format = OutputFormat(fmt_in)

    def conf_fmt(fmt: OutputFormat) -> None:
        if fmt == OutputFormat.JSON:
            _init_output_json_settings(config)
        elif fmt == OutputFormat.TABLE:
            _init_output_table_settings(config)
        elif fmt == OutputFormat.JSONSCHEMA:
            _init_output_jsonschema_settings(config)
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
        "JSON indent",
        default=oconf.indent,
        show_default=True,
    )

    oconf.sort_keys = Confirm.ask(
        "Sort JSON keys",
        default=oconf.sort_keys,
        show_default=True,
    )


def _init_output_table_settings(config: HarborCLIConfig) -> None:
    """Initialize table output settings."""
    _print_output_title(OutputFormat.TABLE)

    oconf = config.output.table

    oconf.max_depth = IntPrompt.ask(
        "Max number of subtables (leave empty for unlimited)",
        default=oconf.max_depth,
        show_default=True,
    )

    oconf.description = Confirm.ask(
        "Show description column",
        default=oconf.description,
        show_default=True,
    )


def _init_output_jsonschema_settings(config: HarborCLIConfig) -> None:
    """Initialize JSON Schema output settings."""
    pass
    # TODO: Implement this if we get JSON Schema-specific settings


def _print_output_title(fmt: OutputFormat) -> None:
    fmt_repr = output_format_repr(fmt)
    console.print(f"\nOutput Configuration ({fmt_repr})", style=TITLE_STYLE)
