from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st
from pydantic import BaseModel
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from .._strategies import COMPACT_TABLE_MODELS
from harbor_cli.format import OutputFormat
from harbor_cli.output import render
from harbor_cli.output.render import render_json
from harbor_cli.output.render import render_result
from harbor_cli.output.render import render_table
from harbor_cli.state import State


# The actual testing of the render functions is done in test_render_<format>()
def test_render_result_json(mocker: MockerFixture, state: State) -> None:
    """Test that we can render a result."""
    spy = mocker.spy(render, "render_json")
    state.config.output.format = OutputFormat.JSON
    result = {"a": 1}
    render_result(result)
    spy.assert_called_once()


def test_render_result_table(mocker: MockerFixture, state: State) -> None:
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
def test_render_json(
    capsys: CaptureFixture, state: State, inp: Any, expected: str
) -> None:
    state.config.output.JSON.indent = 2
    render_json(inp)
    out, _ = capsys.readouterr()
    assert out == expected + "\n"


def test_render_table(capsys: CaptureFixture, state: State) -> None:
    # FIXME: not sure how to test this
    render_table({"a": 1})
    out, _ = capsys.readouterr()
    assert out not in ["", "\n"]


@given(st.one_of(COMPACT_TABLE_MODELS))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_render_table_compact_mock(
    state: State, renderable: BaseModel | list[BaseModel]
) -> None:
    """Test that we can render a result as a compact table."""
    # NOTE: we cannot use the mocker fixture from pytest-mock here, because
    # it will not work with the @given decorator.
    # The mocker fixture is not reset between examples and will cause
    # the test to fail. So we have to manually set up the mocks.
    #
    # This also applies to test_render_table_full_mock()

    full_table_mock = MagicMock()
    compact_table_mock = MagicMock()

    with patch("harbor_cli.output.render.render_table_full", full_table_mock), patch(
        "harbor_cli.output.render.render_table_compact", compact_table_mock
    ):
        # Activate compact table mode
        state.config.output.format = OutputFormat.TABLE
        state.config.output.table.compact = True
        render_table(renderable)

        # Check our spies
        compact_table_mock.assert_called_once()
        full_table_mock.assert_not_called()


def test_render_table_compact_fallback(mocker: MockerFixture, state: State) -> None:
    """Tests that a model with no compact table implementation is rendered
    via the fallback full table implementation."""
    # We can use the pytest-mock mocker fixture here since we don't use hypothesis
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


@given(st.one_of(COMPACT_TABLE_MODELS))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_render_table_full_mock(
    state: State, renderable: BaseModel | list[BaseModel]
) -> None:
    """Test that we can render a result as a full table."""
    full_table_mock = MagicMock()
    compact_table_mock = MagicMock()

    with patch("harbor_cli.output.render.render_table_full", full_table_mock), patch(
        "harbor_cli.output.render.render_table_compact", compact_table_mock
    ):
        # Deactivate compact tables
        state.config.output.format = OutputFormat.TABLE
        state.config.output.table.compact = False
        render_table(renderable)

        # Check our spies
        compact_table_mock.assert_not_called()
        full_table_mock.assert_called_once()
