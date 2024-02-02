from __future__ import annotations

import functools
import sys
from typing import Callable
from typing import TYPE_CHECKING
from typing import TypeVar

import keyring
from keyring.errors import KeyringError
from keyring.errors import PasswordDeleteError
from keyring.errors import PasswordSetError
from typing_extensions import ParamSpec

from harbor_cli.exceptions import KeyringUnsupportedError
from harbor_cli.logs import logger
from harbor_cli.output.console import info
from harbor_cli.output.console import warning

if TYPE_CHECKING:
    from keyring.backend import KeyringBackend

KEYRING_SERVICE_NAME = "harbor_cli"
_KEYRING_DUMMY_USER = "test_user"
_KEYRING_DUMMY_PASSWORD = "test_password"


class DummyPasswordNoMatchError(Exception):
    """Raised when the keyring dummy password does not match."""


@functools.lru_cache(maxsize=1)
def keyring_supported() -> bool:
    """Very naively checks if we can use keyring on the current system.

    We set a dummy password and then try to retrieve it. If we get the same
    password back, we assume that keyring is supported."""
    try:
        backend = get_backend()
        logger.debug("Using keyring backend: %s", backend)
    except KeyringError as e:
        if sys.platform == "darwin":
            if (
                isinstance(e, (PasswordSetError, PasswordDeleteError))
                and e.__context__
                and e.__context__.args
                and e.__context__.args[0] == -25244
            ):
                return _handle_keyring_error_25244_macos(e)
        else:
            logger.error("Keyring error: %s", e)
        return False
    except Exception as e:
        logger.error(
            "Unknown error when checking keyring availability: %s", e, exc_info=True
        )
        return False
    else:
        return True


def _handle_keyring_error_25244_macos(e: KeyringError) -> bool:
    """Handles macOS keyring error -25244 (errSecInvalidOwnerEdit error) when setting
    a password

    This very likely happens if we try to access the keyring from an application
    that is not signed with the same certificate as the one that created the keychain
    item initially.

    See: https://developer.apple.com/forums/thread/69841
    See: https://github.com/python-poetry/poetry/issues/2692#issuecomment-1382387632
    """
    actions = {
        PasswordSetError: "set",
        PasswordDeleteError: "delete",
    }
    action = actions.get(type(e), "access")

    warning(
        f"An error occurred while trying to {action} a password in your keyring.\n"
        f"Please delete any passwords related to [i]{KEYRING_SERVICE_NAME}[/] from your keyring "
        "and try again.\n"
        "If this issue persists, please report it and disable keyring in your config file.\n"
        "Run [i]harbor cli-config path[/] to find the location of your config file."
    )
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


def get_backend() -> KeyringBackend:
    return keyring.get_keyring()


def clear_supported_cache() -> None:
    """Clears the keyring availability cache."""
    keyring_supported.cache_clear()
