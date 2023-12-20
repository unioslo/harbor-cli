from __future__ import annotations

import os

import pytest
import typer
from pytest_mock import MockFixture

from .conftest import PartialInvoker
from harbor_cli.format import OutputFormat
from harbor_cli.models import BaseModel
from harbor_cli.output import render
from harbor_cli.state import State


def test_repl_reset_between_commands(
    app: typer.Typer,
    state: State,
    mocker: MockFixture,
    invoke: PartialInvoker,
) -> None:
    """Test that the REPL resets the state between commands."""
    # We should be starting with the default output format (table)
    state.config.output.format = OutputFormat.TABLE

    # Spy on render functions to check if they're called
    render_json_spy = mocker.spy(render, "render_json")
    render_table_spy = mocker.spy(render, "render_table")

    # just add a command so we don't need to mock the API
    class MockResult(BaseModel):
        foo: str = "bar"
        baz: int = 123

    @app.command("test-cmd")
    def test_cmd(ctx: typer.Context) -> None:
        return render.render_result(MockResult(), ctx)

    # Set output format to table before running
    state.config.output.format = OutputFormat.TABLE
    res = invoke("repl", input="--format json test-cmd\ntest-cmd\n:q\n")
    assert res.exit_code == 0

    # Each render function should have been called once
    render_json_spy.assert_called_once()
    render_table_spy.assert_called_once()

    # The output format should have been reset to default
    assert state.config.output.format == OutputFormat.TABLE
