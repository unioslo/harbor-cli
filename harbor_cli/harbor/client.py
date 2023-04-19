from __future__ import annotations

from typing import TYPE_CHECKING

from harborapi import HarborAsyncClient

if TYPE_CHECKING:
    from ..config import HarborCLIConfig

_CLIENT = None  # type: HarborAsyncClient | None


def get_client(config: HarborCLIConfig) -> HarborAsyncClient:
    global _CLIENT
    if _CLIENT is None:
        # Instantiate harbor client with credentials dict from config
        _CLIENT = HarborAsyncClient(
            **(config.harbor.credentials),
            validate=config.harbor.validate_data,
            raw=config.harbor.raw_mode,
            verify=config.harbor.verify_ssl,
        )
    # Ensure we use the latest config values (for REPL mode)
    _CLIENT.raw = config.harbor.raw_mode
    _CLIENT.validate = config.harbor.validate_data
    # TODO: credentials are only handled on CLI startup, so we
    # need to find a way to pass new credentials to the client
    # Need to add `auth` or `update_credentials` method to HarborAsyncClient
    return _CLIENT
