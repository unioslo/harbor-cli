from __future__ import annotations

from typing import Callable
from typing import TypeVar

import keyring
from typing_extensions import ParamSpec

from ..logs import logger
from ..output.console import error
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
            logger.debug("Keyring is supported on this platform.")
            return True
        else:
            raise keyring.errors.KeyringError
    except keyring.errors.KeyringError as e:
        logger.warning(f"Keyring is not supported on this platform: {e}")
        return False


KEYRING_SUPPORTED = check_keyring_support()

# These functions are not safe to call if keyring is not supported!
# Functions should always check KEYRING_SUPPORTED before calling them.

P = ParamSpec("P")
T = TypeVar("T")


def warn_unsupported(f: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if not KEYRING_SUPPORTED:
            error("Keyring is not supported on this platform.")
            return None
        return f(*args, **kwargs)

    return wrapper


@warn_unsupported
def get_password(username: str) -> str | None:
    return keyring.get_password(KEYRING_SERVICE_NAME, username)


@warn_unsupported
def set_password(username: str, password: str) -> None:
    keyring.set_password(KEYRING_SERVICE_NAME, username, password)
    info("Added password to keyring.")
