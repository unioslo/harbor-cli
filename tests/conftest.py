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
from typer.testing import CliRunner
from typer.testing import Result

from harbor_cli.config import HarborCLIConfig
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


@pytest.fixture
def invoke(app, config_file: Path) -> PartialInvoker:
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
    return request.param


@pytest.fixture(scope="function", params=list(OutputFormat))
def output_format_arg(output_format: OutputFormat) -> list[str]:
    return ["--format", output_format.value]
