from __future__ import annotations

import copy
from pathlib import Path

import keyring
import pytest
import tomli
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from .conftest import requires_keyring
from .conftest import requires_no_keyring
from harbor_cli.config import HarborCLIConfig
from harbor_cli.config import HarborSettings
from harbor_cli.config import load_config
from harbor_cli.config import load_toml_file
from harbor_cli.config import sample_config
from harbor_cli.config import save_config
from harbor_cli.config import TableSettings
from harbor_cli.config import TableStyleSettings
from harbor_cli.utils.keyring import set_password


def test_save_config(tmp_path: Path, config: HarborCLIConfig) -> None:
    conf_path = tmp_path / "config.toml"
    save_config(config, conf_path)
    assert conf_path.exists()


def test_load_config(tmp_path: Path, config: HarborCLIConfig) -> None:
    conf_path = tmp_path / "config.toml"
    save_config(config, conf_path)
    loaded = load_config(conf_path)
    assert loaded.toml() == config.toml()


def test_load_toml_file(tmp_path: Path) -> None:
    contents = """\
[harbor]
url = "https://harbor.example.com/api/v2.0"

[output]
format = "table"
"""
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(contents)
    loaded = load_toml_file(toml_file)
    assert loaded == {
        "harbor": {"url": "https://harbor.example.com/api/v2.0"},
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


def test_harbor_cli_config_not_from_file() -> None:
    """Assert the config object has the config_file field even
    if not loaded from a file"""
    config = HarborCLIConfig()
    assert config is not None
    assert config.config_file is None


def test_harbor_cli_config_from_file_not_exists(tmp_path: Path) -> None:
    f = tmp_path / "test_harbor_cli_config_from_file_not_exists_config.toml"
    assert not f.exists()
    with pytest.raises(FileNotFoundError):
        HarborCLIConfig.from_file(f, create=False)


def test_harbor_cli_config_from_file_create(tmp_path: Path) -> None:
    f = tmp_path / "test_harbor_cli_config_from_file_create_config.toml"
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
    assert all(c == "*" for c in str(h.secret))  # secret string
    h.secret = ""  # both username and password is required
    assert not h.has_auth_method


@requires_keyring
def test_harbor_is_authable_keyring() -> None:
    h = HarborSettings(username="admin", keyring=True)
    set_password(h.username, "password")

    # secret field will not be populated by keyring assignment
    assert h.secret.get_secret_value() != "password"

    # secret_value fetches from keyring if it is enabled
    assert h.secret_value == "password"  # fetches from keyring

    assert h.has_auth_method
    assert h.credentials["username"] == "admin"
    assert h.credentials["secret"] == "password"


@requires_no_keyring
def test_harbor_is_authable_no_keyring() -> None:
    with pytest.raises(keyring.errors.KeyringError) as exc_info:
        h = HarborSettings(username="admin", secret="ignored", keyring=True)
        h.secret_value  # raises
    assert "not supported" in str(exc_info.value).casefold()
    h = HarborSettings(username="admin", secret="password", keyring=False)
    assert h.secret_value == "password"
    assert h.has_auth_method


def test_harbor_is_authable_basicauth() -> None:
    h = HarborSettings(basicauth="dXNlcm5hbWU6cGFzc3dvcmQK")
    assert h.has_auth_method
    # TODO: rename to basicauth when harborapi supports it
    assert h.credentials["basicauth"] == "dXNlcm5hbWU6cGFzc3dvcmQK"


def test_harbor_is_authable_credentials_file(tmp_path: Path) -> None:
    f = tmp_path / "credentials.json"
    f.write_text("test")  # no validation of the file contents
    h = HarborSettings(credentials_file=f)
    assert h.has_auth_method
    assert h.credentials["credentials_file"] == f


def test_secretstr_assignment() -> None:
    """We want to make sure assignment to SecretStr fields with regular
    strings are still converted to SecretStr, so we don't leak credentials
    that have been assigned to the field _after_ instantiation."""

    h = HarborSettings(username="admin", secret="password")
    assert all(c == "*" for c in str(h.secret))
    h.secret = "newpassword"
    assert all(c == "*" for c in str(h.secret))


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


def _write_table_style_rows(
    path: Path, rows: list[str] | str | None
) -> TableStyleSettings:
    """Helper function for creating a config with the option
    `output.table.style.rows` and returning the parsed TableStyleSettings
    object."""
    conf_path = path / "config.toml"
    if rows is not None:
        if isinstance(rows, str):
            rows = f'rows = "{rows}"'
        else:
            rows = "rows = " + str(rows)  # str representation of list
    else:
        rows = ""
    conf_path.write_text(f"[output.table.style]\n{rows}")
    config = HarborCLIConfig.from_file(conf_path)
    return config.output.table.style


def test_tablestylesettings_rows_array(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, ["blue", "red"])
    assert styleconf.rows == ("blue", "red")


def test_tablestylesettings_rows_array_size3(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, ["blue", "red", "green"])
    assert styleconf.rows == ("blue", "red")


def test_tablestylesettings_rows_array_size1(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, ["blue"])
    assert styleconf.rows == ("blue", "blue")


def test_tablestylesettings_rows_string(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, "blue")
    assert styleconf.rows == ("blue", "blue")


def test_tablestylesettings_rows_emptystring(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, "")
    assert styleconf.rows is None


def test_tablestylesettings_rows_emptyarray(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, [])
    assert styleconf.rows is None


def test_tablestylesettings_rows_omit(tmp_path: Path) -> None:
    styleconf = _write_table_style_rows(tmp_path, None)
    assert styleconf.rows is None


def test_tablestylesettings_empty_string_is_none(tmp_path: Path) -> None:
    toml = """[output.table.style]
title = ""
header = ""
rows = ""
border = ""
footer = ""
caption = ""
expand = true
show_header = true
bool_emoji = false"""

    # Pass in just the table style TOML and rely on defaults for the rest
    conf_file = tmp_path / "config.toml"
    conf_file.write_text(toml)
    config = HarborCLIConfig.from_file(conf_file)
    styleconf = config.output.table.style
    assert styleconf.rows is None
    assert styleconf.title is None
    assert styleconf.header is None
    assert styleconf.border is None
    assert styleconf.footer is None
    assert styleconf.caption is None


@given(st.one_of(st.none(), st.text(), st.lists(st.text(), min_size=1)))
def test_tablestylesettings_fuzz(rows: list[str] | str | None) -> None:
    """Fuzzing with hypothesis."""
    styleconf = TableStyleSettings(rows=rows)
    if rows and any(s for s in rows):
        if isinstance(rows, list):
            assert styleconf.rows == (rows[0], rows[1] if len(rows) > 1 else rows[0])
        elif isinstance(rows, str):
            assert styleconf.rows == (rows, rows)
    else:
        assert styleconf.rows is None


def test_sample_config() -> None:
    s = sample_config()
    config_dict = tomli.loads(s)
    assert config_dict  # not empty, not None


@pytest.mark.parametrize("expose_secrets", [True, False])
def test_harbor_cli_config_toml_expose_secrets(
    config: HarborCLIConfig, expose_secrets: bool, tmp_path: Path
) -> None:
    """Test that the toml() expose_secrets parameter works as expected."""
    creds_file = tmp_path / "somefile"
    creds_file.touch()

    config.harbor.username = "someuser"
    config.harbor.secret = "somepassword"
    config.harbor.basicauth = "somebasicauth"
    config.harbor.credentials_file = creds_file

    toml_str = config.toml(expose_secrets=expose_secrets)
    if expose_secrets:
        assert "somepassword" in toml_str
        assert "somebasicauth" in toml_str
        assert "somefile" in toml_str
    else:
        assert "somepassword" not in toml_str
        assert "somebasicauth" not in toml_str
        assert "somefile" not in toml_str
        assert "***" in toml_str  # don't be too specific about the number of stars


def test_dunder_copy(config: HarborCLIConfig, tmp_path: Path) -> None:
    """Test that the __copy__ method works as expected with excluded fields."""
    mock_path = tmp_path / "config.toml"
    mock_path.touch()
    config.config_file = mock_path
    assert config.config_file is not None
    copied = config.__copy__()
    assert hasattr(copied, "config_file")
    assert copied.config_file == config.config_file

    copied_with_copy = copy.copy(config)
    assert copied_with_copy.config_file == config.config_file


def test_dunder_deepcopy(config: HarborCLIConfig, tmp_path: Path) -> None:
    """Test that the __deepcopy__ method works as expected with excluded fields."""
    mock_path = tmp_path / "config.toml"
    mock_path.touch()
    config.config_file = mock_path
    assert config.config_file is not None
    copied = config.__deepcopy__({})
    assert hasattr(copied, "config_file")
    assert copied.config_file == config.config_file

    copied_with_copy = copy.deepcopy(config)
    assert copied_with_copy.config_file == config.config_file
