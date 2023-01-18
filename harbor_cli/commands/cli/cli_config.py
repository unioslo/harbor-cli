from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Optional

import typer
from pydantic import Extra

from ...config import HarborCLIConfig
from ...output.console import console
from ...output.console import err_console
from ...output.console import exit_err
from ...output.console import success
from ...output.render import render_result
from ...output.table.anysequence import AnySequence
from ...state import state

# Create a command group
app = typer.Typer(
    name="cli-config",
    help="Manage CLI configuration.",
    no_args_is_help=True,
)


def render_config(config: HarborCLIConfig, as_toml: bool) -> None:
    if as_toml:
        console.print(config.toml(), markup=False)
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


@app.command("keys")
def get_cli_config_keys(ctx: typer.Context) -> None:
    """Show the current CLI configuration."""

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


@app.command("set", no_args_is_help=True)
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
        True,
        "--show/--no-show",
        help="Show the current configuration after setting the value.",
    ),
    as_toml: bool = typer.Option(
        True,
        "--toml/--no-toml",
        help="Render config as TOML if [green]--show[/] is set. Overrides [green]--format[/].",
    ),
) -> None:
    """Set a key in the CLI configuration."""
    attrs = []
    if "." in key:
        attrs = key.split(".")

    try:
        # temporarily forbid extra fields, so typos raise an error
        state.config.__config__.extra = Extra.forbid
        if attrs:
            obj = getattr(state.config, attrs[0])
            for attr in attrs[1:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], value)
        else:
            setattr(state.config, key, value)
    except (
        ValueError,  # pydantic raises ValueError for unknown fields
        AttributeError,
    ):
        err_console.print(f"Invalid key: [red]{key}[/]")
    finally:
        state.config.__config__.extra = Extra.forbid

    if not session:
        state.config.save(path=path)

    if show_config:
        render_config(state.config, as_toml)


@app.command("write")
def write_session_config(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Path to save configuration file. Overrides the config's current path.",
    ),
) -> None:
    """Write the current [bold]session[/] configuration to disk. Used to save
    changes made with [green]harbor cli-config set --session[/] in REPL mode."""
    save_path = path or state.config.config_file
    if save_path is None:
        exit_err(
            "No path specified and no path found in current configuration. Use [green]--path[/] to specify a path."
        )
    state.config.save(path=save_path)
    success(f"Saved configuration to [green]{save_path}[/]")
