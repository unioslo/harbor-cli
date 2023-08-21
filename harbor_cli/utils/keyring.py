from __future__ import annotations

from typing import Callable
from typing import Final
from typing import TypeVar

import keyring
from typing_extensions import ParamSpec

from ..logs import logger
from ..output.console import info

KEYRING_SERVICE_NAME = "harbor_cli"


def check_keyring_support():
    dummy_user = "test_user"
    dummy_password = "test_password"
    try:
        # Set and get a dummy password to test the backend
        keyring.set_password(KEYRING_SERVICE_NAME, dummy_user, dummy_password)
        password = keyring.get_password(KEYRING_SERVICE_NAME, dummy_user)

        # Check if the password was correctly retrieved
        if password == dummy_password:
            return True
        else:
            raise keyring.errors.KeyringError
    # TODO: make this error handling more robust. Differentiate between different
    # keyring errors and handle them accordingly.
    except keyring.errors.KeyringError as e:
        logger.warning(f"Keyring is not supported on this platform: {e}")
        return False


KEYRING_SUPPORTED: Final[bool] = check_keyring_support()

P = ParamSpec("P")
T = TypeVar("T")


def require_keyring(f: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if not KEYRING_SUPPORTED:
            raise keyring.errors.KeyringError(
                "Keyring is not supported on this platform."
            )  # NOTE: should this be just an exit_err() call?
        return f(*args, **kwargs)

    return wrapper


@require_keyring
def get_password(username: str) -> str | None:
    return keyring.get_password(KEYRING_SERVICE_NAME, username)


@require_keyring
def set_password(username: str, password: str) -> None:
    keyring.set_password(KEYRING_SERVICE_NAME, username, password)
    info("Added password to keyring.")
