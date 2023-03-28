from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Optional

import typer

from ...config import HarborCLIConfig
from ...logs import logger
from ...output.console import console
from ...output.console import exit_err
from ...output.console import success
from ...output.render import render_result
from ...output.table.anysequence import AnySequence
from ...state import state
from ...style import render_cli_command
from ...style import render_cli_value
from ...style import render_config_option
from ...utils.utils import forbid_extra

# Create a command group
app = typer.Typer(
    name="cli-config",
    help="Manage CLI configuration.",
    no_args_is_help=True,
)


def render_config(config: HarborCLIConfig, as_toml: bool) -> None:
    if as_toml:
        console.print(config.toml(expose_secrets=False), markup=False)
    else:
        render_result(config)


@app.command("get")
def get_cli_config(
    ctx: typer.Context,
    as_toml: bool = typer.Option(
        True,
        "--toml/--no-toml",
        help="Show the current configuration in TOML format after setting the value. Overrides --format.",
    ),
) -> None:
    """Show the current CLI configuration."""
    render_config(state.config, as_toml)
    logger.info(f"Source: {state.config.config_file}")


@app.command(
    "keys",
    help=f"Show all config keys that can be modified with {render_cli_command('cli-config set')}.",
)
def get_cli_config_keys(ctx: typer.Context) -> None:
    def get_fields(field: dict[str, Any], current: str) -> list[str]:
        fields = []
        if isinstance(field, dict):
            for sub_key, sub_value in field.items():
                f = get_fields(sub_value, f"{current}.{sub_key}")
                fields.extend(f)
        else:
            fields.append(current)
        return fields

    ff = []
    d = state.config.dict()
    for key, value in d.items():
        if isinstance(value, dict):
            ff.extend(get_fields(value, key))
        else:
            ff.append(key)  # no subkeys

    render_result(AnySequence(values=ff, title="Config Keys"))


@app.command(
    "set",
    no_args_is_help=True,
    help=f"Modify a CLI configuration value. Use {render_cli_command('cli-config keys')} to see all available keys.",
)
def set_cli_config(
    ctx: typer.Context,
    key: str = typer.Argument(
        ...,
        help="Key to set. Subkeys can be specified using dot notation. e.g. [green]'harbor.url'[/]",
    ),
    value: str = typer.Argument(..., help="Value to set."),
    path: Path = typer.Option(None, "--path", help="Path to save configuration file."),
    session: bool = typer.Option(
        False,
        "--session",
        help="Set the value in the current session only. The value will not be saved to disk. Only useful in REPL mode.",
    ),
    show_config: bool = typer.Option(
        False,
        "--show/--no-show",
        help="Show the current configuration after setting the value.",
    ),
    as_toml: bool = typer.Option(
        True,
        "--toml/--no-toml",
        help="Render updated config as TOML in terminal if [green]--show[/] is set. Overrides global option [green]--format[/].",
    ),
) -> None:
    attrs = []
    if "." in key:
        attrs = key.split(".")

    # Forbid extra temporarily so typos trigger errors
    with forbid_extra(state.config):
        try:
            if attrs:
                obj = getattr(state.config, attrs[0])
                for attr in attrs[1:-1]:
                    obj = getattr(obj, attr)
                setattr(obj, attrs[-1], value)
            else:
                setattr(state.config, key, value)
        except (
            ValueError,  # pydantic raises ValueError for unknown fields
            AttributeError,  # getattr call failed
        ):
            exit_err(f"Invalid config key: {key!r}")

    if not session:
        state.config.save(path=path)

    if show_config:
        render_config(state.config, as_toml)
    success(f"Set {render_config_option(key)} to {render_cli_value(value)}")


@app.command(
    "write",
    help=(
        "Write the current [bold]session[/] configuration to disk. "
        f"Used to save changes made with {render_cli_command('cli-config set --session')} in REPL mode."
    ),
)
def write_session_config(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Path to save configuration file. Uses current config file path if not specified.",
    ),
) -> None:
    save_path = path or state.config.config_file
    if save_path is None:
        exit_err(
            "No path specified and no path found in current configuration. Use [green]--path[/] to specify a path."
        )
    state.config.save(path=save_path)
    success(f"Saved configuration to [green]{save_path}[/]")


# TODO: reload config
