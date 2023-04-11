from __future__ import annotations

from typing import TYPE_CHECKING

from harborapi import HarborAsyncClient

from ..logs import logger
from ..output.prompts import str_prompt

if TYPE_CHECKING:
    from ..config import HarborCLIConfig

# It's unlikely that we will authenticate with multiple
# Harbor instances, so keeping it in a dict is probably overkill

_CLIENTS = {}  # type: dict[str, HarborAsyncClient]


def get_client(config: HarborCLIConfig) -> HarborAsyncClient:
    if _CLIENTS.get(config.harbor.url) is None:
        # Instantiate harbor client with credentials dict from config
        _CLIENTS[config.harbor.url] = HarborAsyncClient(
            **(config.harbor.credentials),
            validate=config.harbor.validate_data,
            raw=config.harbor.raw_mode,
            verify=config.harbor.verify_ssl,
        )
    client = _CLIENTS[config.harbor.url]
    # Ensure we use the latest config values (when running in REPL mode)
    # When running in REPL mode, we re-use the same client instance, but
    # we might pass in new config values
    client.raw = config.harbor.raw_mode
    client.validate = config.harbor.validate_data
    # TODO: credentials are only handled on CLI startup, so we
    # need to find a way to pass new credentials to the client
    return client


def setup_client(config: HarborCLIConfig) -> HarborAsyncClient:
    """Setup the HarborAsyncClient for the application."""
    # We want to log all problems before prompting for input,
    # so we do these checks pre-emptively
    has_url = True if config.harbor.url else False
    has_auth = True if config.harbor.has_auth_method else False
    if not has_url:
        logger.warning("Harbor API URL missing from configuration file.")
    if not has_auth:
        logger.warning("Harbor authentication method missing from configuration file.")

    if not has_url:
        config.harbor.url = str_prompt("Harbor API URL")

    # We need one of the available auth methods to be specified
    # If not, prompt for username and password
    if not has_auth:
        # TODO: refactor this so we can re-use username and password
        # prompts from commands.cli.init!
        if not config.harbor.username:
            config.harbor.username = str_prompt("Username")
        if not config.harbor.secret:
            config.harbor.secret = str_prompt("Password", password=True)  # type: ignore # pydantic.SecretStr

    return get_client(config)
