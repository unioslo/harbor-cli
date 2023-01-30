from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from harbor_cli.output import render
from harbor_cli.output.format import OutputFormat
from harbor_cli.output.render import render_json
from harbor_cli.output.render import render_result
from harbor_cli.output.render import render_table
from harbor_cli.state import state


# The actual testing of the render functions is done in test_render_<format>()
def test_render_result_json(mocker: MockerFixture) -> None:
    """Test that we can render a result."""
    spy = mocker.spy(render, "render_json")
    state.config.output.format = OutputFormat.JSON
    result = {"a": 1}
    render_result(result)
    spy.assert_called_once()


def test_render_result_table(mocker: MockerFixture) -> None:
    """Test that we can render a result."""
    spy = mocker.spy(render, "render_table")
    state.config.output.format = OutputFormat.TABLE
    result = {"a": 1}
    render_result(result)
    spy.assert_called_once()


class SomeModel(BaseModel):
    a: int
    b: str


# assume JSON indent is 2
@pytest.mark.parametrize(
    "inp,expected",
    [
        ({}, "{}"),
        ([], "[]"),
        ({"a": 1}, '{\n  "a": 1\n}'),
        ({"a": 1}, '{\n  "a": 1\n}'),
        (SomeModel(a=1, b="2"), '{\n  "a": 1,\n  "b": "2"\n}'),
    ],
)
def test_render_json(capsys: CaptureFixture, inp: Any, expected: str) -> None:
    state.config.output.JSON.indent = 2
    render_json(inp)
    out, _ = capsys.readouterr()
    assert out == expected + "\n"


def test_render_table(capsys: CaptureFixture) -> None:
    # FIXME: not sure how to test this
    render_table({"a": 1})
    out, _ = capsys.readouterr()
    assert out not in ["", "\n"]


def test_render_table_compact_mock(
    mocker: MockerFixture, compact_table_renderable: BaseModel
) -> None:
    """Test that we can render a result as a compact table."""
    # FIXME: getting the following error when attempting to create mock
    # for render_table and render_table_compact when using hypothesis strategy:
    # TypeError: __name__ must be set to a string object

    full_table_spy = mocker.spy(render, "render_table_full")
    compact_table_spy = mocker.spy(render, "render_table_compact")

    state.config.output.format = OutputFormat.TABLE
    state.config.output.table.compact = True
    render_table(compact_table_renderable)

    # Check our spies
    compact_table_spy.assert_called_once()
    full_table_spy.assert_not_called()


def test_render_table_compact_fallback(mocker: MockerFixture) -> None:
    """Tests that a model with no compact table implementation is rendered
    via the fallback full table implementation."""
    full_table_spy = mocker.spy(render, "render_table_full")
    compact_table_spy = mocker.spy(render, "render_table_compact")

    # Activate compact table mode
    state.config.output.format = OutputFormat.TABLE
    state.config.output.table.compact = True

    model = SomeModel(a=1, b="2")
    render_table(model)

    # Check our spies
    compact_table_spy.assert_called_once()  # we try to call it before falling back
    full_table_spy.assert_called()


# TODO: fix not being able to combine mocker and hypothesis
def test_render_table_full_mock(
    mocker: MockerFixture, compact_table_renderable: BaseModel
) -> None:
    """Test that we can render a result as a compact table."""
    # FIXME: getting the following error when attempting to create mock
    # for render_table and render_table_compact:
    # TypeError: __name__ must be set to a string object

    full_table_spy = mocker.spy(render, "render_table_full")
    compact_table_spy = mocker.spy(render, "render_table_compact")

    # Deactivate compact tables
    state.config.output.format = OutputFormat.TABLE
    state.config.output.table.compact = False
    render_table(compact_table_renderable)

    # Check our spies
    compact_table_spy.assert_not_called()
    full_table_spy.assert_called()
