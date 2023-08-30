from __future__ import annotations

import functools
from typing import Callable
from typing import TypeVar

import keyring
from typing_extensions import ParamSpec

from ..logs import logger
from ..output.console import info

KEYRING_SERVICE_NAME = "harbor_cli"


class KeyringUnsupportedError(Exception):
    pass


@functools.lru_cache(maxsize=1)
def keyring_supported():
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
            raise keyring.errors.KeyringError(
                "Keyring backend did not return the correct password."
            )
    # TODO: make this error handling more robust. Differentiate between different
    # keyring errors and handle them accordingly.
    except (keyring.errors.KeyringError, KeyringUnsupportedError) as e:
        logger.debug(f"Keyring is not supported on this platform: {e}", exc_info=True)
        return False


P = ParamSpec("P")
T = TypeVar("T")


def require_keyring(f: Callable[P, T]) -> Callable[P, T]:
    """Decorator that ensures keyring is supported on the current platform."""

    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if not keyring_supported():
            raise KeyringUnsupportedError("Keyring is not supported on this platform.")
        return f(*args, **kwargs)

    return wrapper


@require_keyring
def get_password(username: str) -> str | None:
    return keyring.get_password(KEYRING_SERVICE_NAME, username)


@require_keyring
def set_password(username: str, password: str) -> None:
    keyring.set_password(KEYRING_SERVICE_NAME, username, password)
    info("Added password to keyring.")


@require_keyring
def delete_password(username: str) -> None:
    keyring.delete_password(KEYRING_SERVICE_NAME, username)
    info("Deleted password from keyring.", user=username)
