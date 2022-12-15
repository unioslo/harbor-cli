from __future__ import annotations

from typing import NoReturn

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

from .logs import logger
from .output.console import exit_err


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
            self,
            f"Artifact string {s} is not in the correct format. "
            "Expected format: [domain/]<project>/<repo>{@sha256:<digest>,:<tag>}",
        )


MESSAGE_BADREQUEST = "400 Bad request: {method} {url}. Check your input. If you think this is a bug, please report it."
MESSAGE_UNAUTHORIZED = "401 Unauthorized: {method} {url}. Check your credentials, and make sure you have permissions to access the resource."
MESSAGE_FORBIDDEN = "403 Forbidden: {method} {url}. Check your credentials, and make sure you have permissions to access the resource."
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


class Default(dict):
    """Dict subclass used for str.format_map() to provide default.
    Missing keys are replaced with the key surrounded by curly braces."""

    def __missing__(self, key):
        return "{" + key + "}"


def handle_status_error(e: StatusError) -> NoReturn:
    """Handles an HTTP status error from the Harbor API and exits with
    the appropriate message.
    """
    # It's not _guaranteed_ that the StatusError has a __cause__, but
    # in practice it should always have one. It is up to harborapi to
    # ensure that this is the case, but it's currently not guaranteed.
    # In the cases where it's not, we just exit with the default message.
    if not e.__cause__:
        exit_err(str(e))

    url = e.__cause__.request.url
    method = e.__cause__.request.method
    httpx_message = e.__cause__.args[0]

    # Print out all errors from the API
    for error in e.errors:
        logger.error(f"{error.code}: {error.message}")

    # Exception has custom message if its message is different from the
    # underlying HTTPX exception's message
    msg = e.args[0]
    has_default_message = httpx_message == msg

    # Use custom message from our mapping if the exception has default msg
    if has_default_message:
        template = MESSAGE_MAPPING.get(type(e), None)
        if template:
            msg = template.format_map(Default(url=url, method=method))
    exit_err(msg)
