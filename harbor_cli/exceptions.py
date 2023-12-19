from __future__ import annotations

from typing import Any
from typing import cast
from typing import Dict
from typing import Mapping
from typing import NoReturn
from typing import Optional
from typing import Protocol
from typing import runtime_checkable
from typing import Type

from harborapi.exceptions import BadRequest
from harborapi.exceptions import Conflict
from harborapi.exceptions import Forbidden
from harborapi.exceptions import InternalServerError
from harborapi.exceptions import MethodNotAllowed
from harborapi.exceptions import NotFound
from harborapi.exceptions import PreconditionFailed
from harborapi.exceptions import StatusError
from harborapi.exceptions import Unauthorized
from harborapi.exceptions import UnsupportedMediaType
from httpx._exceptions import CookieConflict
from httpx._exceptions import HTTPError
from httpx._exceptions import InvalidURL
from httpx._exceptions import StreamError
from pydantic import ValidationError


class HarborCLIError(Exception):
    """Base class for all exceptions."""


class ConfigError(HarborCLIError):
    """Error loading the configuration file."""


class ConfigFileNotFoundError(ConfigError, FileNotFoundError):
    """Configuration file not found."""


class DirectoryCreateError(HarborCLIError, OSError):
    """Error creating a required program directory."""


class CredentialsError(HarborCLIError):
    """Error loading credentials."""


class OverwriteError(HarborCLIError, FileExistsError):
    """Error overwriting an existing file."""


class ArtifactNameFormatError(HarborCLIError):
    def __init__(self, s: str) -> None:
        super().__init__(
            f"Artifact string {s} is not in the correct format. "
            "Expected 'project/repo:tag' OR 'project/repo@sha256:digest'",
        )


class Exiter(Protocol):
    """Protocol class for exit function that can be passed to an
    exception handler function.

    See Also
    --------
    [harbor_cli.exceptions.HandleFunc][]
    """

    def __call__(
        self, msg: str, code: int = ..., prefix: str = ..., **extra: Any
    ) -> NoReturn:
        ...


@runtime_checkable
class HandleFunc(Protocol):
    """Interface for exception handler functions.

    They take any exception and an Exiter function as the arguments
    and exit with the appropriate message after running any necessary
    cleanup and/or logging.
    """

    def __call__(self, e: Any, exiter: Exiter) -> NoReturn:
        ...


MESSAGE_BADREQUEST = "400 Bad request: {method} {url}. Check your input. If you think this is a bug, please report it."
MESSAGE_UNAUTHORIZED = "401 Unauthorized: {method} {url}. Check your credentials."
MESSAGE_FORBIDDEN = "403 Forbidden: {method} {url}. Make sure you have permissions to access the resource."
MESSAGE_NOTFOUND = "404 Not Found: {method} {url}. Resource not found."
MESSAGE_METHODNOTALLOWED = "405 Method Not Allowed: {method} {url}. This is either a bug, or a problem with your server or credentials."
MESSAGE_CONFLICT = "409 Conflict: {method} {url}. Resource already exists."
MESSAGE_PRECONDITIONFAILED = "412 Precondition Failed: {method} {url} Check your input. If you think this is a bug, please report it."
MESSAGE_UNSUPPORTEDMEDIATYPE = "415 Unsupported Media Type: {method} {url}. Check your input. If you think this is a bug, please report it."
MESSAGE_INTERNALSERVERERROR = "500 Internal Server Error: {method} {url}. Check your input. If you think this is a bug, please report it."

MESSAGE_MAPPING = {
    BadRequest: MESSAGE_BADREQUEST,
    Unauthorized: MESSAGE_UNAUTHORIZED,
    Forbidden: MESSAGE_FORBIDDEN,
    NotFound: MESSAGE_NOTFOUND,
    MethodNotAllowed: MESSAGE_METHODNOTALLOWED,
    Conflict: MESSAGE_CONFLICT,
    PreconditionFailed: MESSAGE_PRECONDITIONFAILED,
    UnsupportedMediaType: MESSAGE_UNSUPPORTEDMEDIATYPE,
    InternalServerError: MESSAGE_INTERNALSERVERERROR,
}


class Default(Dict[str, Any]):
    """Dict subclass used for str.format_map() to provide default.
    Missing keys are replaced with the key surrounded by curly braces."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def handle_status_error(e: StatusError, exiter: Exiter) -> NoReturn:
    """Handles an HTTP status error from the Harbor API and exits with
    the appropriate message.
    """
    from .output.console import exit_err  # avoid circular import
    from .logs import logger

    # It's not _guaranteed_ that the StatusError has a __cause__, but
    # in practice it should always have one. It is up to harborapi to
    # ensure that this is the case, but it's currently not guaranteed.
    # In the cases where it's not, we just exit with the default message.
    if not e.__cause__:
        exit_err(str(e))

    url = e.__cause__.request.url
    method = e.__cause__.request.method
    httpx_message = e.__cause__.args[0]

    # Log all errors from the API
    for error in e.errors:
        logger.error(f"{error.code}: {error.message}")

    # Exception has custom message if its message is different from the
    # underlying HTTPX exception's message
    msg = e.args[0]
    has_default_message = httpx_message == msg

    # Use custom message from our mapping if the exception has default HTTPX msg
    # and we have a custom message for the exception type
    # The default HTTPX messages are not very helpful.
    if has_default_message:
        template = MESSAGE_MAPPING.get(type(e), None)
        if template:
            msg = template.format_map(Default(url=url, method=method))
    exit_err(msg)


def handle_validationerror(e: ValidationError, exiter: Exiter) -> NoReturn:
    """Handles a pydantic ValidationError and exits with the appropriate message."""
    exiter(f"Failed to validate data from API: {e}", errors=e.errors(), exc_info=True)


def handle_notraceback(e: HarborCLIError, exiter: Exiter) -> NoReturn:
    """Handles an exception (no traceback)."""
    exiter(str(e), exc_info=True)


EXC_HANDLERS: Mapping[Type[Exception], HandleFunc] = {
    ValidationError: handle_validationerror,
    StatusError: handle_status_error,
    HarborCLIError: handle_notraceback,
    HTTPError: handle_notraceback,
    InvalidURL: handle_notraceback,
    CookieConflict: handle_notraceback,
    StreamError: handle_notraceback,
}


def get_exception_handler(type_: Type[Exception]) -> Optional[HandleFunc]:
    """Returns the exception handler for the given exception type."""
    handler = EXC_HANDLERS.get(type_, None)
    if handler:
        return handler
    if type_.__bases__:
        for base in type_.__bases__:
            handler = get_exception_handler(base)
            if handler:
                return handler
    return None


def handle_exception(e: Exception) -> NoReturn:
    """Handles an exception and exits with the appropriate message."""
    from .output.console import exit_err  # avoid circular import

    # TODO: resolve circular imports by lazy-importing OverwriteError in output.render

    exiter = cast(Exiter, exit_err)

    handler = get_exception_handler(type(e))
    if not handler:
        raise e
    handler(e, exiter)
