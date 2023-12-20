from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ...app import app
from ...config import create_config
from ...config import DEFAULT_CONFIG_FILE
from ...config import HarborCLIConfig
from ...config import HarborSettings
from ...config import save_config
from ...exceptions import ConfigError
from ...exceptions import OverwriteError
from ...format import output_format_emoji
from ...format import output_format_repr
from ...format import OutputFormat
from ...harbor.common import prompt_basicauth
from ...harbor.common import prompt_credentials_file
from ...harbor.common import prompt_username_secret
from ...logs import LogLevel
from ...output.console import console
from ...output.console import error
from ...output.console import exit_err
from ...output.console import info
from ...output.console import success
from ...output.console import warning
from ...output.formatting import path_link
from ...output.prompts import bool_prompt
from ...output.prompts import int_prompt
from ...output.prompts import path_prompt
from ...output.prompts import str_prompt
from ...state import get_state
from ...style import render_cli_option
from ...style.style import render_cli_command
from ...utils.keyring import keyring_supported
from ...utils.keyring import set_password

state = get_state()

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
        msg = f"Config file already exists ({path_link(p)})"
        if wizard:
            warning(msg)
        else:
            exit_err(msg)
        config_path = None
    else:
        info(f"Created config file at {config_path}")

    config = run_config_wizard(config_path)
    state.config = config

    # NOTE: should we only call this if state.is_client_loaded?
    # But the worst case scenario is this has no effect, right?
    state.authenticate_harbor()


def run_config_wizard(config_path: Optional[Path] = None) -> HarborCLIConfig:
    """Loads the config file, and runs the configuration wizard.

    Delegates to subroutines for each config category, that modify
    the loaded config object in-place."""
    conf_exists = config_path is None

    try:
        config = HarborCLIConfig.from_file(config_path)
    except Exception as e:
        exit_err(
            f"Failed to load config: {e}. Run {render_cli_command('harbor init --overwrite')} to create a new config file.",
            exc_info=True,
        )

    assert config.config_file is not None

    console.print()
    console.rule(":sparkles: Harbor CLI Configuration Wizard :mage:")

    # FIXME: we have likely created the config file at this point, so
    # the logic below is incorrect.

    # We only ask the user to configure mandatory sections if the config
    # file existed prior to running wizard.
    # Otherwise, we force the user to configure Harbor settings, because
    # we can't do anything without them.
    if not conf_exists or bool_prompt("\nConfigure harbor settings?", default=False):
        init_harbor_settings(config)
        console.print()

    if bool_prompt("Configure advanced Harbor settings?", default=False):
        _init_advanced_harbor_settings(config)
        console.print()

    if bool_prompt("Configure general settings?", default=False):
        init_general_settings(config)
        console.print()

    # These categories are optional, and as such we always ask the user
    if bool_prompt("Configure output settings?", default=False):
        init_output_settings(config)
        console.print()

    if bool_prompt("Configure REPL settings?", default=False):
        init_repl_settings(config)
        console.print()

    if bool_prompt("Configure logging settings?", default=False):
        init_logging_settings(config)
        console.print()

    conf_path = config_path or config.config_file
    if not conf_path:
        raise ConfigError("Could not determine config file path.")
    save_config(config, conf_path)
    success("Configuration complete! :tada:")
    info(f"Saved config to {path_link(conf_path)}")
    return config


def init_harbor_settings(config: HarborCLIConfig) -> None:
    """Initialize Harbor settings."""
    print_title("Harbor Settings", emoji=":ship:")

    hconf = config.harbor
    config.harbor.url = str_prompt(
        "Harbor API URL (e.g. https://harbor.example.com/api/v2.0)",
        default=hconf.url,
        show_default=True,
    )

    # Determine auth method
    base_msg = "Authentication method [bold magenta](\[u]sername/password, \[b]asic auth, \[f]ile, \[s]kip)[/]"
    choices = ["u", "b", "f", "s"]
    if hconf.has_auth_method:
        default_choice = "s"
    else:
        default_choice = "u"
    auth_method = str_prompt(
        base_msg, choices=choices, default=default_choice, show_choices=False
    )

    # Clear all previous credentials if we provide new credentials
    hconf_pre = hconf.model_copy()  # use for defaults in prompts
    if not auth_method == "s":
        hconf.clear_credentials()

    if auth_method == "u":
        set_username_secret(hconf, hconf_pre.username, hconf_pre.secret_value)
    elif auth_method == "b":
        hconf.basicauth = prompt_basicauth(hconf_pre.basicauth.get_secret_value())  # type: ignore # pydantic.SecretStr
    elif auth_method == "f":
        hconf.credentials_file = prompt_credentials_file(hconf_pre.credentials_file)

    # Explain what will happen if no auth method is provided
    if not hconf.has_auth_method:
        warning(
            "No authentication info provided. "
            "You will be prompted for username and password when required.",
        )


def set_username_secret(
    hconf: HarborSettings, current_username: str, current_secret: str
) -> None:
    username, secret = prompt_username_secret(current_username, current_secret)
    if keyring_supported():
        _set_username_secret_keyring(hconf, username, secret)
    else:
        _set_username_secret_config(hconf, username, secret)


def _set_username_secret_config(
    hconf: HarborSettings, username: str, secret: str
) -> None:
    """Stores both username and config in config file.
    Insecure fallback in case keyring is not supported."""
    hconf.username = username
    hconf.secret = secret  # type: ignore # pydantic.SecretStr
    hconf.keyring = False


def _set_username_secret_keyring(
    hconf: HarborSettings, username: str, secret: str
) -> None:
    """Set username and secret using keyring.
    Stores the secret in the keyring and the username in the config file."""
    hconf.username = username
    set_password(username, secret)
    hconf.keyring = True


def _init_advanced_harbor_settings(config: HarborCLIConfig) -> None:
    """Initialize advanced Harbor settings."""
    print_title("Advanced Harbor Settings", emoji=":wrench:")

    hconf = config.harbor

    hconf.verify_ssl = bool_prompt(
        "Verify SSL certificates?",
        default=hconf.verify_ssl,
        show_default=True,
    )

    # NOTE: Enabling these _WILL_ cause certain commands to fail
    # So we leave them as config file-only options for now that
    # can be enabled manually.
    # hconf.validate_data = bool_prompt(
    #     "Validate data received from Harbor?",
    #     default=hconf.validate_data,
    #     show_default=True,
    # )

    # hconf.raw_mode = bool_prompt(
    #     "Enable raw mode (print raw responses from API)?",
    #     default=hconf.raw_mode,
    #     show_default=True,
    # )

    # TODO: implement timeout, retry, retry_delay
    # hconf.timeout = int_prompt(
    #     "Timeout (seconds)",
    #     default=hconf.timeout,
    #     show_default=True,
    # )
    # hconf.retry = int_prompt(
    #     "Retry count",
    #     default=hconf.retry,
    #     show_default=True,
    # )
    # hconf.retry_delay = int_prompt(
    #     "Retry delay (seconds)",
    #     default=hconf.retry_delay,
    #     show_default=True,
    # )


def init_logging_settings(config: HarborCLIConfig) -> None:
    """Initialize logging settings."""
    print_title("Logging Settings", emoji=":mag:")

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
    print_title("Output Settings", emoji=":desktop_computer:")

    oconf = config.output

    _init_output_format(config)

    # Leading newline to separate from format configuration(s)
    oconf.paging = bool_prompt(
        "\nShow output in pager? (requires 'less' or other pager to be installed and configured)",
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
    """Initialize output format settings."""
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
            error(f"Unknown configuration format {fmt.value}")

    # Configure the chosen format first
    conf_fmt(oconf.format)

    # Optionally configure other formats afterwards
    formats = [f for f in OutputFormat if f != oconf.format]
    for fmt in formats:
        if bool_prompt(
            f"\nConfigure {output_format_repr(fmt)} output settings?", default=False
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

    # Leading newline for subcategory
    if bool_prompt("\nConfigure table style?", default=False):
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

    print_title("REPL Settings", emoji=":arrows_counterclockwise:")

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


def init_general_settings(config: HarborCLIConfig) -> None:
    conf = config.general

    print_title("General Settings")

    conf.confirm_enumeration = bool_prompt(
        "Confirm unconstrained enumeration of resources",
        default=conf.confirm_enumeration,
    )

    conf.confirm_deletion = bool_prompt(
        f"Confirm deletion of resources when {render_cli_option('--force')} is omitted",
        default=conf.confirm_deletion,
    )


def print_title(title: str, emoji: str = ":gear:") -> None:
    e = f"{emoji} " if emoji else ""
    console.print(f"\n{e}{title}", style=TITLE_STYLE)


def _print_output_title(fmt: OutputFormat) -> None:
    title = f"Output Configuration ({output_format_repr(fmt)})"
    emoji = f":desktop_computer: {output_format_emoji(fmt)}"
    print_title(title, emoji=emoji)
