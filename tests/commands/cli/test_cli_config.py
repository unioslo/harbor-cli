from __future__ import annotations

import os
from pathlib import Path

from pytest import LogCaptureFixture

from harbor_cli.config import EnvVar
from harbor_cli.config import HarborCLIConfig
from harbor_cli.format import OutputFormat
from harbor_cli.state import State


# TODO: test more keys and more levels of nesting
def test_cli_config_get_key(invoke, config: HarborCLIConfig, config_file: Path) -> None:
    # We assume the `invoke` fixture uses the `config_file`
    # fixture (which it does at the time of writing), so we can just
    # test against the values in the `config` fixture.
    config.config_file = config_file

    # 1 level of nesting
    assert config.harbor.url is not None
    result = invoke(["cli-config", "get", "harbor.url"])
    assert result.exit_code == 0, result.stderr
    assert result.stdout == config.harbor.url + os.linesep

    # 2 levels of nesting
    assert config.harbor.retry.max_tries is not None
    result = invoke(["cli-config", "get", "harbor.retry.max_tries"])
    assert result.exit_code == 0
    assert result.stdout == str(config.harbor.retry.max_tries) + os.linesep

    # 0 levels of nesting (top-level key) (technically not supported)
    result = invoke(["cli-config", "get", "harbor"])
    assert result.exit_code == 0
    # this will print the harbor settings as a table NOT TOML, and
    # we have no good way (yet) to test that
    # In the future, all config models should be serializable to TOML,
    # so that we can test this.
    for key in config.harbor.model_fields.keys():
        assert key in result.stdout


def test_cli_config_get(
    invoke, config: HarborCLIConfig, tmp_path: Path, config_file: Path
) -> None:
    config.config_file = config_file

    assert config.output.format is not None
    result = invoke(["cli-config", "get"])
    assert result.exit_code == 0, result.stderr

    tmp_config = tmp_path / "config_get.toml"
    with open(tmp_config, "w") as f:
        f.write(result.stdout)
    stdout_config = HarborCLIConfig.from_file(tmp_config)

    # The two configs should be identical with the exception of the config path
    # so we need to make those match before comparing
    stdout_config.config_file = config.config_file

    # Secrets are hidden from the output, so we need to revert them to original
    stdout_config.harbor.secret = config.harbor.secret
    stdout_config.harbor.basicauth = config.harbor.basicauth
    stdout_config.harbor.credentials_file = config.harbor.credentials_file

    assert stdout_config == config


def test_cli_config_set(invoke, state: State, config_file: Path) -> None:
    state.config.config_file = config_file

    state.config.output.format = OutputFormat.TABLE
    result = invoke(["cli-config", "set", "output.format", "json"])
    assert result.exit_code == 0, result.stderr
    assert state.config.output.format == OutputFormat.JSON
    assert (
        state.config.from_file(config_file).output.format == OutputFormat.JSON
    )  # Saved to disk


def test_cli_config_set_session(invoke, state: State, config_file: Path) -> None:
    state.config.config_file = config_file

    state.config.output.format = OutputFormat.TABLE
    result = invoke(["cli-config", "set", "output.format", "json", "--session"])
    assert result.exit_code == 0, result.stderr
    assert state.config.output.format == OutputFormat.JSON  # Changed in session
    assert (
        state.config.from_file(config_file).output.format == OutputFormat.TABLE
    )  # Not saved to disk


def test_env_no_vars(invoke) -> None:
    res = invoke(["cli-config", "env"], env={})  # unset all env vars for this test
    assert res.exit_code == 0
    assert "No environment variables set" in res.stderr


def test_env_var_set(invoke) -> None:
    res = invoke(["cli-config", "env"], env={EnvVar.URL: "https://example.com"})
    assert res.exit_code == 0
    assert "URL" in res.stdout
    assert "https://example.com" in res.stdout
