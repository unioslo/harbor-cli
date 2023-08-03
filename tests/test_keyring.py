from __future__ import annotations

from .conftest import needs_keyring
from harbor_cli.utils.keyring import get_password
from harbor_cli.utils.keyring import set_password


@needs_keyring
def test_set_password():
    set_password("harbor_cli_test_user", "harbor_cli_test_password")


@needs_keyring
def test_get_password():
    # TODO: make this test more robust and deterministic
    assert get_password("harbor_cli_test_user_not_exists") is None
    set_password("harbor_cli_test_user", "harbor_cli_test_password")
    assert get_password("harbor_cli_test_user") == "harbor_cli_test_password"
