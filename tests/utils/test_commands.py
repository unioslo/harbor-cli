from __future__ import annotations

from typing import Optional

import click
import pytest
import typer
from pydantic import BaseModel
from pydantic import Field
from typer import Context
from typer.models import CommandInfo

from harbor_cli.utils.commands import get_app_commands
from harbor_cli.utils.commands import get_command_help
from harbor_cli.utils.commands import get_parent_ctx
from harbor_cli.utils.commands import inject_help
from harbor_cli.utils.commands import inject_resource_options


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
    def sub_sub_app_command(
        argument: str = typer.Argument(..., help="Positional argument"),
        option: Optional[int] = typer.Option(None, "-o", "--option", help="Option"),
    ) -> None:
        pass

    app.add_typer(sub_app, name="sub-app")
    sub_app.add_typer(subsub_app)  # name specified on creation above

    commands = get_app_commands(app)
    assert len(commands) == 3

    # The commands are returned in alphabetical order
    # TODO: test command signature + params when added to CommandSummary
    assert commands[0].name == "sub-app sub-app-command"
    assert commands[0].help == "Sub-app command."

    assert commands[1].name == "sub-app sub-sub-app sub-sub-app-command"
    assert commands[1].help == "Sub-sub-app command."

    assert commands[2].name == "top-app-command"
    assert commands[2].help == "Top-level app command."


def test_inject_help() -> None:
    class TestModel(BaseModel):
        field1: str = Field(..., description="This is field 1.")
        field2: int = Field(..., description="This is field 2.")
        field3: bool = Field(..., description="This is field 3.")

    app = typer.Typer()

    @app.command(name="some-command")
    @inject_help(TestModel)
    def some_command(
        field1: str = typer.Option(...),
        field2: int = typer.Option(...),
        field3: bool = typer.Option(...),
    ) -> None:
        pass

    defaults = some_command.__defaults__
    assert defaults is not None
    assert len(defaults) == 3
    assert defaults[0].help == "This is field 1."
    assert defaults[1].help == "This is field 2."
    assert defaults[2].help == "This is field 3."


def test_inject_help_no_defaults() -> None:
    class TestModel(BaseModel):
        field1: str = Field(..., description="This is field 1.")
        field2: int = Field(..., description="This is field 2.")
        field3: bool = Field(..., description="This is field 3.")

    app = typer.Typer()

    @app.command(name="some-command")
    @inject_help(TestModel)
    def some_command(
        field1: str,
        field2: int,
        field3: bool,
    ) -> None:
        pass

    defaults = some_command.__defaults__
    assert defaults is None


def test_inject_resource_options() -> None:
    app = typer.Typer()

    @app.command(name="some-command")
    @inject_resource_options
    def some_command(
        query: Optional[str],
        sort: Optional[str],
        page: int,
        # with parameter default
        page_size: int = typer.Option(123),
        # ellipsis signifies that we should inject the default
        limit: Optional[int] = ...,
    ) -> None:
        pass

    parameters = some_command.__signature__.parameters
    assert len(parameters) == 5
    assert parameters["query"].default.help == "Query parameters to filter the results."
    assert (
        parameters["sort"].default.help
        == "Sorting order of the results. Example: [green]'name,-id'[/] to sort by name ascending and id descending."
    )
    assert parameters["page"].default.help == "(Advanced) Page to begin fetching from."
    assert (
        parameters["page_size"].default.help
        == "(Advanced) Results to fetch per API call."
    )
    assert parameters["page_size"].default.default == 123
    assert parameters["limit"].default.help == "Maximum number of results to fetch."
    assert (
        parameters["limit"].default.default is None
    )  # ellipsis means default (None in this case) is injected


def test_inject_resource_options_partial_params() -> None:
    app = typer.Typer()

    @app.command(name="some-command")
    @inject_resource_options
    def some_command(
        query: Optional[str],
        page_size: int = typer.Option(123),
    ) -> None:
        pass

    parameters = some_command.__signature__.parameters
    assert len(parameters) == 2
    # can test more granularly if needed


def test_inject_resource_options_strict() -> None:
    app = typer.Typer()

    # Missing parameters will raise an error in strict mode
    with pytest.raises(ValueError):

        @app.command(name="some-command")
        @inject_resource_options(strict=True)
        def some_command(
            query: Optional[str],
            page_size: int = typer.Option(123),
        ) -> None:
            pass


def test_inject_resource_options_no_defaults() -> None:
    app = typer.Typer()

    @app.command(name="some-command")
    @inject_resource_options(use_defaults=False)
    def some_command(
        page_size: int = typer.Option(123),
    ) -> None:
        pass

    parameters = some_command.__signature__.parameters
    assert len(parameters) == 1
    assert parameters["page_size"].default.default != 123
    assert parameters["page_size"].default.default == 10

    # can test more granularly if needed


# TODO: test each resource injection function individually
