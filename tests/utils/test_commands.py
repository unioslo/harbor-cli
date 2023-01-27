from __future__ import annotations

import click
import typer
from typer import Context
from typer.models import CommandInfo

from harbor_cli.utils.commands import get_app_commands
from harbor_cli.utils.commands import get_command_help
from harbor_cli.utils.commands import get_parent_ctx


def test_get_parent_ctx() -> None:
    ctx_top_level = Context(click.Command(name="top-level"))
    ctx_mid_level = Context(click.Command(name="mid-level"))
    ctx_bot_level = Context(click.Command(name="bot-level"))
    ctx_mid_level.parent = ctx_top_level
    ctx_bot_level.parent = ctx_mid_level
    assert get_parent_ctx(ctx_bot_level) == ctx_top_level
    assert get_parent_ctx(ctx_mid_level) == ctx_top_level
    assert get_parent_ctx(ctx_top_level) == ctx_top_level


def test_get_parent_ctx_top_level() -> None:
    ctx_top_level = Context(click.Command(name="top-level"))
    assert get_parent_ctx(ctx_top_level) == ctx_top_level


def test_get_parent_ctx_insane_nesting() -> None:
    ctx = Context(click.Command(name="top-level"))
    prev = ctx
    for i in range(100):
        c = Context(click.Command(name=f"level-{i}"))
        c.parent = prev
        prev = c
    assert get_parent_ctx(c) == ctx


def test_get_command_help_typer() -> None:
    # Typer does some magic in its decorator, so we can't just add the @app.command
    # decorator and pass the function to get_command_help.
    # Instead we mock a CommandInfo object with this function as the callback.
    def some_command():
        """This is a test command."""
        pass

    some_command_info = CommandInfo(name="some-command", callback=some_command)
    assert get_command_help(some_command_info) == "This is a test command."

    some_command_info.help = "Override help from docstring."
    assert get_command_help(some_command_info) == "Override help from docstring."


def test_get_command_help_click() -> None:
    """Test get_command_help using a click Command object (not intended behavior,
    but it has the same interface as typer.models.CommandInfo)"""

    @click.command()
    def some_command():
        """This is a test command."""
        pass

    assert get_command_help(some_command) == "This is a test command."  # type: ignore

    some_command.help = "Override help from docstring."
    assert get_command_help(some_command) == "Override help from docstring."  # type: ignore


def test_get_app_commands() -> None:
    app = typer.Typer(name="top-app")
    sub_app = typer.Typer()  # name specified when adding to app below
    subsub_app = typer.Typer(name="sub-sub-app")

    @app.command(name="top-app-command")
    def app_command() -> None:
        """Top-level app command."""
        pass

    @sub_app.command(name="sub-app-command")
    def sub_app_command() -> None:
        """Sub-app command."""
        pass

    # Help text in decorator
    @subsub_app.command(name="sub-sub-app-command", help="Sub-sub-app command.")
    def sub_sub_app_command() -> None:
        pass

    app.add_typer(sub_app, name="sub-app")
    sub_app.add_typer(subsub_app)  # name specified on creation above

    commands = get_app_commands(app)
    assert len(commands) == 3

    # Sub-app is found first, and its command is found before the sub-sub-app's
    assert commands[0].name == "sub-app sub-app-command"
    assert commands[0].help == "Sub-app command."

    assert commands[1].name == "sub-app sub-sub-app sub-sub-app-command"
    assert commands[1].help == "Sub-sub-app command."

    # After we are done recursing, we should be at the top-level app again
    assert commands[2].name == "top-app-command"
    assert commands[2].help == "Top-level app command."
