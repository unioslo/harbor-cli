from __future__ import annotations

from functools import partial
from typing import Any
from typing import IO
from typing import Mapping
from typing import Protocol

import click
import pytest
import typer
from typer.testing import CliRunner
from typer.testing import Result

from harbor_cli.main import app as main_app
from harbor_cli.output.format import OutputFormat

runner = CliRunner()


@pytest.fixture(scope="session")
def app():
    return main_app


class PartialInvoker(Protocol):
    """Protocol for a partial function that invokes a CLI command."""

    def __call__(
        self,
        args: str | list[str] | None,
        input: bytes | str | IO | None = None,
        env: Mapping[str, str] | None = None,
        catch_exceptions: bool = True,
        color: bool = False,
        **extra: Any,
    ) -> Result:
        ...


@pytest.fixture
def invoke(app) -> PartialInvoker:
    """Partial function for invoking a CLI command with the app as the entrypoint."""
    p = partial(runner.invoke, app)
    return p


@pytest.fixture
def mock_ctx() -> typer.Context:
    """Create a mock context."""
    return typer.Context(click.Command(name="mock"))


@pytest.fixture(name="output_format", scope="function", params=list(OutputFormat))
def _output_format(request: pytest.FixtureRequest) -> OutputFormat:
    return request.param


@pytest.fixture(scope="function", params=list(OutputFormat))
def output_format_arg(output_format: OutputFormat) -> list[str]:
    return ["--format", output_format.value]
