from __future__ import annotations

from enum import Enum
from enum import IntEnum
from pathlib import Path

import pytest
import pytest_mock
import typer
from harborapi.utils import get_basicauth
from keyring.errors import PasswordDeleteError
from typer.testing import Result

from .conftest import PartialInvoker
from .conftest import requires_keyring
from harbor_cli.config import EnvVar
from harbor_cli.format import OutputFormat
from harbor_cli.state import State
from harbor_cli.utils.keyring import delete_password
from harbor_cli.utils.keyring import set_password


def test_envvars(
    invoke: PartialInvoker,
    app: typer.Typer,
    tmp_path: Path,
    state: State,
    config_file: Path,
) -> None:
    @app.command("test-cmd")
    def test_cmd(ctx: typer.Context) -> None:
        print("ok!")
        return 0

    def inv(envvar: EnvVar, value: str) -> Result:
        res = invoke(
            ["test-cmd"], env={str(envvar): value, str(EnvVar.CONFIG): str(config_file)}
        )
        assert res.exit_code == 0
        return res

    inv(EnvVar.URL, "https://example.com/api/v2.0")
    assert state.config.harbor.url == "https://example.com/api/v2.0"

    inv(EnvVar.USERNAME, "admin")
    assert state.config.harbor.username == "admin"

    inv(EnvVar.SECRET, "secret")
    assert state.config.harbor.secret.get_secret_value() == "secret"

    inv(EnvVar.BASICAUTH, "123")
    assert state.config.harbor.basicauth.get_secret_value() == "123"

    cred_file = tmp_path / "creds"
    cred_file.write_text("admin\nsecret")
    inv(EnvVar.CREDENTIALS_FILE, str(cred_file))
    assert state.config.harbor.credentials_file == cred_file

    inv(EnvVar.HARBOR_VALIDATE_DATA, "1")
    assert state.config.harbor.validate_data is True
    inv(EnvVar.HARBOR_VALIDATE_DATA, "0")
    assert state.config.harbor.validate_data is False

    inv(EnvVar.HARBOR_VERIFY_SSL, "1")
    assert state.config.harbor.verify_ssl is True
    inv(EnvVar.HARBOR_VERIFY_SSL, "0")
    assert state.config.harbor.verify_ssl is False

    inv(EnvVar.HARBOR_RETRY_ENABLED, "1")
    assert state.config.harbor.retry.enabled is True
    inv(EnvVar.HARBOR_RETRY_ENABLED, "0")
    assert state.config.harbor.retry.enabled is False

    inv(EnvVar.HARBOR_RETRY_MAX_TRIES, "3")
    assert state.config.harbor.retry.max_tries == 3

    inv(EnvVar.HARBOR_RETRY_MAX_TIME, "300")
    assert state.config.harbor.retry.max_time == 300

    inv(EnvVar.TABLE_DESCRIPTION, "1")
    assert state.config.output.table.description is True
    inv(EnvVar.TABLE_DESCRIPTION, "0")
    assert state.config.output.table.description is False

    inv(EnvVar.TABLE_MAX_DEPTH, "5")
    assert state.config.output.table.max_depth == 5

    inv(EnvVar.TABLE_COMPACT, "1")
    assert state.config.output.table.compact is True
    inv(EnvVar.TABLE_COMPACT, "0")
    assert state.config.output.table.compact is False

    inv(EnvVar.JSON_INDENT, "4")
    assert state.config.output.JSON.indent == 4

    inv(EnvVar.JSON_SORT_KEYS, "1")
    assert state.config.output.JSON.sort_keys is True
    inv(EnvVar.JSON_SORT_KEYS, "0")
    assert state.config.output.JSON.sort_keys is False

    inv(EnvVar.OUTPUT_FORMAT, "json")
    assert state.config.output.format == OutputFormat.JSON

    inv(EnvVar.PAGING, "1")
    assert state.config.output.paging is True
    inv(EnvVar.PAGING, "0")
    assert state.config.output.paging is False

    inv(EnvVar.PAGER, "less")
    assert state.config.output.pager == "less"

    inv(EnvVar.CONFIRM_DELETION, "1")
    assert state.config.general.confirm_deletion is True
    inv(EnvVar.CONFIRM_DELETION, "0")
    assert state.config.general.confirm_deletion is False

    inv(EnvVar.CONFIRM_ENUMERATION, "1")
    assert state.config.general.confirm_enumeration is True
    inv(EnvVar.CONFIRM_ENUMERATION, "0")
    assert state.config.general.confirm_enumeration is False


HARBOR_CLI_TEST_USERNAME = "harbor_cli_test_user"


@pytest.fixture(scope="function")
def reset_keyring() -> None:
    """Clears the test user from the keyring.
    Should only be used by functions decorated with @requires_keyring"""
    yield
    try:
        delete_password(HARBOR_CLI_TEST_USERNAME)
    except PasswordDeleteError as e:
        # Ignore if password was deleted by the test
        if "not found" not in str(e):  # pragma: no cover
            raise


class SecretMethod(IntEnum):
    OPTION = 0
    ENV = 1
    KEYRING = 2
    CONFIG = 3


@requires_keyring
def test_auth_precedence(
    invoke: PartialInvoker,
    app: typer.Typer,
    tmp_path: Path,
    state: State,
    config_file: Path,
    reset_keyring: None,
    mocker: pytest_mock.MockFixture,
) -> None:
    @app.command("test-cmd")
    def test_cmd(ctx: typer.Context) -> None:
        async def some_func() -> None:
            pass

        # We need to call state.run() in order to trigger the re-authentication
        state.run(some_func())
        return 0

    env_common = {
        str(EnvVar.USERNAME): HARBOR_CLI_TEST_USERNAME,
        str(EnvVar.URL): "https://example.com/api/v2.0",
    }

    # Method and expected pw sorted by precedence
    secret_values = {
        SecretMethod.OPTION: "option",
        SecretMethod.ENV: "env",
        SecretMethod.KEYRING: "keyring",
        SecretMethod.CONFIG: "config",
    }
    for method in secret_values:
        # Configure from lowest to highest precedence
        if method <= SecretMethod.CONFIG:
            state.config.harbor.secret = secret_values[SecretMethod.CONFIG]
            state.config.harbor.keyring = False
        if method <= SecretMethod.KEYRING:
            set_password(HARBOR_CLI_TEST_USERNAME, secret_values[SecretMethod.KEYRING])
            state.config.harbor.keyring = True
        else:
            delete_password(HARBOR_CLI_TEST_USERNAME)
        if method <= SecretMethod.ENV:
            env = {str(EnvVar.SECRET): secret_values[SecretMethod.ENV], **env_common}
        else:
            env = env_common
        if method.value <= SecretMethod.OPTION:
            args = ["--secret", secret_values[SecretMethod.OPTION]]
        else:
            args = []

        res = invoke(
            [*args, "test-cmd"],
            env=env,
        )
        assert res.exit_code == 0, res.stderr

        expect_pw = secret_values[method]
        # Check config credentials
        assert state.config.harbor.secret_value == expect_pw
        # Check client credentials
        assert (
            state.client.basicauth.get_secret_value()
            == get_basicauth(HARBOR_CLI_TEST_USERNAME, expect_pw).get_secret_value()
        ), f"method: {method.name}"
