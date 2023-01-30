from __future__ import annotations

from pathlib import Path

import pytest
import tomli
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from harbor_cli.config import HarborCLIConfig
from harbor_cli.config import HarborSettings
from harbor_cli.config import load_config
from harbor_cli.config import load_toml_file
from harbor_cli.config import sample_config
from harbor_cli.config import save_config
from harbor_cli.config import TableSettings


def test_save_config(tmp_path: Path, config: HarborCLIConfig) -> None:
    conf_path = tmp_path / "config.toml"
    save_config(config, conf_path)
    assert conf_path.exists()


def test_load_config(tmp_path: Path, config: HarborCLIConfig) -> None:
    conf_path = tmp_path / "config.toml"
    save_config(config, conf_path)
    loaded = load_config(conf_path)
    assert loaded.toml() == config.toml()


def test_load_toml_file(tmp_path: Path, config: HarborCLIConfig) -> None:
    contents = """\
[harbor]
url = "https://harbor.example.com"

[output]
format = "table"
"""
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(contents)
    loaded = load_toml_file(toml_file)
    assert loaded == {
        "harbor": {"url": "https://harbor.example.com"},
        "output": {"format": "table"},
    }


@given(st.builds(HarborCLIConfig))
def test_harbor_cli_config_fuzz(config: HarborCLIConfig) -> None:
    """Fuzzing with hypothesis."""
    assert config is not None  # not a lot to specifically test here


def test_harbor_cli_config_from_file(config_file: Path) -> None:
    assert config_file.exists()
    config = HarborCLIConfig.from_file(config_file)
    assert config is not None


def test_harbor_cli_config_from_file_not_exists(tmp_path: Path) -> None:
    f = tmp_path / "config.toml"
    assert not f.exists()
    with pytest.raises(FileNotFoundError):
        HarborCLIConfig.from_file(f, create=False)


def test_harbor_cli_config_from_file_create(tmp_path: Path) -> None:
    f = tmp_path / "config.toml"
    assert not f.exists()
    conf = HarborCLIConfig.from_file(f, create=True)
    assert conf is not None
    assert f.exists()


@given(st.builds(HarborSettings))
def test_harbor_settings(settings: HarborSettings) -> None:
    assert settings is not None
    assert settings.credentials is not None


def test_harbor_settings_credentials_file_empty_string() -> None:
    h = HarborSettings(credentials_file="")
    assert h.credentials_file is None


def test_harbor_settings_credentials_file_not_exists(tmp_path: Path) -> None:
    f = tmp_path / "credentials.json"
    with pytest.raises(ValidationError) as exc_info:
        HarborSettings(credentials_file=f)
    e = exc_info.exconly()
    assert "exist" in e.casefold()


def test_harbor_settings_credentials_file_is_dir(tmp_path: Path) -> None:
    f = tmp_path / "testdir"
    f.mkdir()
    with pytest.raises(ValidationError) as exc_info:
        HarborSettings(credentials_file=f)
    e = exc_info.exconly()
    assert "file" in e.casefold()


def test_harbor_is_authable_not() -> None:
    h = HarborSettings()
    assert not h.has_auth_method


def test_harbor_is_authable_username() -> None:
    h = HarborSettings(username="admin", secret="password")
    assert h.has_auth_method
    assert h.credentials["username"] == "admin"
    assert h.credentials["secret"] == "password"
    h.secret = ""  # both username and password is required
    assert not h.has_auth_method


def test_harbor_is_authable_basicauth() -> None:
    h = HarborSettings(basicauth="dXNlcm5hbWU6cGFzc3dvcmQK")
    assert h.has_auth_method
    # TODO: rename to basicauth when harborapi supports it
    assert h.credentials["credentials"] == "dXNlcm5hbWU6cGFzc3dvcmQK"


def test_harbor_is_authable_credentials_file(tmp_path: Path) -> None:
    f = tmp_path / "credentials.json"
    f.write_text("test")  # no validation of the file contents
    h = HarborSettings(credentials_file=f)
    assert h.has_auth_method
    assert h.credentials["credentials_file"] == f


@given(st.builds(TableSettings))
def test_table_settings(table: TableSettings) -> None:
    """Fuzzing with hypothesis."""
    assert table is not None
    # Max depth is either None or a non-negative integer
    assert table.max_depth is None or table.max_depth >= 0


def test_table_settings_max_depth_negative() -> None:
    t = TableSettings(max_depth=-1)
    assert t.max_depth == 0


def test_table_settings_max_depth_none() -> None:
    t = TableSettings(max_depth=None)
    assert t.max_depth == 0


def test_table_settings_max_depth_nonnegative() -> None:
    t = TableSettings(max_depth=123)
    assert t.max_depth == 123


def test_sample_config() -> None:
    s = sample_config()
    config_dict = tomli.loads(s)
    assert config_dict  # not empty, not None
