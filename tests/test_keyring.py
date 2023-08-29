from __future__ import annotations

import keyring
import pytest

from .conftest import requires_keyring
from .conftest import requires_no_keyring
from harbor_cli.utils.keyring import get_password
from harbor_cli.utils.keyring import KeyringUnsupportedError
from harbor_cli.utils.keyring import set_password


@requires_keyring
def test_set_password():
    set_password("harbor_cli_test_user", "harbor_cli_test_password")


@requires_keyring
def test_get_password():
    # TODO: make this test more robust and deterministic
    assert get_password("harbor_cli_test_user_not_exists") is None
    set_password("harbor_cli_test_user", "harbor_cli_test_password")
    assert get_password("harbor_cli_test_user") == "harbor_cli_test_password"


@requires_no_keyring
def test_set_password_no_keyring():
    with pytest.raises(KeyringUnsupportedError) as exc_info:
        set_password("harbor_cli_test_user", "harbor_cli_test_password")
    assert "not supported" in str(exc_info.value)


@requires_no_keyring
def test_get_password_no_keyring():
    with pytest.raises(KeyringUnsupportedError) as exc_info:
        get_password("harbor_cli_test_user")
    assert "not supported" in str(exc_info.value)
