from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any
from typing import IO
from typing import Mapping
from typing import Protocol

import click
import pytest
import typer
from pydantic import BaseModel
from typer.testing import CliRunner
from typer.testing import Result

from harbor_cli.main import app as main_app  # noreorder

# We can't import these before main is imported, because of circular imports
from harbor_cli.config import HarborCLIConfig
from harbor_cli.output.format import OutputFormat
from ._utils import compact_renderables

runner = CliRunner()


@pytest.fixture(scope="session")
def app():
    return main_app


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:  # type: ignore
    """Setup the CLI config for testing."""
    conf_path = tmp_path / "config.toml"
    conf = HarborCLIConfig.from_file(conf_path, create=True)
    # These are required to run commands
    conf.harbor.url = "https://harbor.example.com"
    conf.harbor.username = "admin"
    conf.harbor.secret = "password"
    conf.save(conf_path)
    yield conf_path


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
def invoke(app: typer.Typer, config_file: Path) -> PartialInvoker:
    """Partial function for invoking a CLI command with the app as the entrypoint,
    and the temp config as the config file."""
    p = partial(runner.invoke, app, env={"HARBOR_CLI_CONFIG": str(config_file)})
    return p


@pytest.fixture
def mock_ctx() -> typer.Context:
    """Create a mock context."""
    return typer.Context(click.Command(name="mock"))


@pytest.fixture(name="output_format", scope="function", params=list(OutputFormat))
def _output_format(request: pytest.FixtureRequest) -> OutputFormat:
    """Fixture for testing all output formats."""
    return request.param


@pytest.fixture(scope="function", params=list(OutputFormat))
def output_format_arg(output_format: OutputFormat) -> list[str]:
    """Parametrized fixture that returns the CLI argument for all output formats."""
    return ["--format", output_format.value]


@pytest.fixture(scope="function", params=compact_renderables)
def compact_table_renderable(request: pytest.FixtureRequest) -> BaseModel:
    """Fixture for testing compact table renderables that can be instantiated with no arguments."""
    return request.param()
