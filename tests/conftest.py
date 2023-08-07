from __future__ import annotations

import os
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import Any
from typing import Generator
from typing import IO
from typing import Mapping
from typing import Protocol

import click
import pytest
import typer
from _pytest.logging import LogCaptureFixture
from harborapi import HarborAsyncClient
from loguru import logger
from typer.testing import CliRunner
from typer.testing import Result

from harbor_cli import state
from harbor_cli.config import EnvVar
from harbor_cli.config import HarborCLIConfig
from harbor_cli.format import OutputFormat
from harbor_cli.main import app as main_app
from harbor_cli.utils.keyring import KEYRING_SUPPORTED

runner = CliRunner(mix_stderr=False)


@pytest.fixture(scope="session")
def app():
    return main_app


@pytest.fixture(scope="session", autouse=True)
def dumb_terminal():
    """Test in a dumb terminal, so that we don't get ANSI escape codes in the output."""
    os.environ["TERM"] = "dumb"
    os.environ["NO_COLOR"] = "1"
    os.environ.pop("COLORTERM", None)
    os.environ.pop("FORCE_COLOR", None)


@pytest.fixture(scope="function")
def config() -> HarborCLIConfig:
    conf = HarborCLIConfig()
    # These are required to run commands
    conf.harbor.url = "https://harbor.example.com/api/v2.0"
    conf.harbor.username = "admin"
    conf.harbor.secret = "password"  # type: ignore
    return conf


@pytest.fixture()
def config_file(tmp_path: Path, config: HarborCLIConfig) -> Path:  # type: ignore
    """Setup the CLI config for testing."""
    conf_path = tmp_path / "config.toml"
    config.save(conf_path)
    yield conf_path


@pytest.fixture(scope="function")
def harbor_client(config: HarborCLIConfig) -> HarborAsyncClient:
    """Fixture for testing the Harbor client."""
    return HarborAsyncClient(
        username=config.harbor.username,
        secret=config.harbor.secret.get_secret_value(),
        url=config.harbor.url,
    )


@pytest.fixture(name="state", scope="function")
def _state_fixture(
    config: HarborCLIConfig, harbor_client: HarborAsyncClient, config_file: Path
) -> state.State:
    """Fixture for testing the state."""
    st = state.get_state()  # Initialize the state
    st.config = config
    st.client = harbor_client
    yield state.get_state()


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
    p = partial(runner.invoke, app, env={str(EnvVar.CONFIG): str(config_file)})
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


@pytest.fixture(scope="function", autouse=True)
def revert_state_config(state: state.State) -> Generator[None, None, None]:
    """Reverts the global state config back to its original value after the test is run."""
    original_config = deepcopy(state.config)
    yield
    state.config = original_config


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


requires_keyring = pytest.mark.skipif(
    not KEYRING_SUPPORTED, reason="Keyring is not supported on this platform."
)
requires_no_keyring = pytest.mark.skipif(
    KEYRING_SUPPORTED, reason="Test requires keyring to be unsupported."
)
