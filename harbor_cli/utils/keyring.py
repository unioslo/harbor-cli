from __future__ import annotations

import functools
from typing import Callable
from typing import TYPE_CHECKING
from typing import TypeVar

import keyring
from keyring.errors import KeyringError
from keyring.errors import NoKeyringError
from typing_extensions import ParamSpec

from harbor_cli.exceptions import KeyringUnsupportedError
from harbor_cli.logs import logger
from harbor_cli.output.console import info

if TYPE_CHECKING:
    from keyring.backend import KeyringBackend

KEYRING_SERVICE_NAME = "harbor_cli"


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
        return True
    except NoKeyringError:
        pass  # does not need to be logged
    except KeyringError as e:
        logger.error("Keyring error: %s", e, exc_info=True)
    except Exception as e:
        logger.error(
            "Unknown error when checking keyring availability: %s", e, exc_info=True
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
