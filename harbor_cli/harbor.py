from __future__ import annotations

from harborapi import HarborAsyncClient

from .config import HarborCLIConfig

# It's unlikely that we will authenticate with multiple
# Harbor instances, so keeping it in a dict is probably superfluous.
_CLIENTS = {}  # type: dict[str, HarborAsyncClient]


def get_client(config: HarborCLIConfig) -> HarborAsyncClient:
    if _CLIENTS.get(config.harbor.url) is None:
        # Instantiate harbor client with credentials dict from config
        _CLIENTS[config.harbor.url] = HarborAsyncClient(**(config.harbor.credentials))
    return _CLIENTS[config.harbor.url]
