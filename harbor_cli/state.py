from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypeVar

from harborapi import HarborAsyncClient
from pydantic import BaseModel
from rich.console import Console

# This module generally shouldn't import from other local modules
# because it's widely used throughout the application, and we don't want
# to create circular import issues.

if TYPE_CHECKING:
    from .config import HarborCLIConfig
    from .cache import Cache

T = TypeVar("T")


class CommonOptions(BaseModel):
    """Options that can be used with any command.

    These options are not specific to any particular command.
    """

    # Output
    verbose: bool = False
    with_stdout: bool = False
    # File
    output_file: Optional[Path] = None
    no_overwrite: bool = False

    class Config:
        extra = "allow"


class State:
    """Object that encapsulates the current state of the application.
    Holds the current configuration, harbor client, and other stateful objects.
    """

    options: CommonOptions = CommonOptions()
    loop: asyncio.AbstractEventLoop
    repl: bool = False

    # Attributes (exposed as properties)
    _cache = None  # type: Cache | None
    _config = None  # type: HarborCLIConfig | None
    _client = None  # type: HarborAsyncClient | None
    _console = None  # type: Console | None

    # Flags to determine if the config or client have been loaded
    _config_loaded: bool = False
    _client_loaded: bool = False

    def __init__(
        self,
        config: HarborCLIConfig | None = None,
        client: HarborAsyncClient | None = None,
    ) -> None:
        """Initialize the state object.

        Parameters
        ----------
        config : HarborCLIConfig | None
            Config to override default config with.
        client : HarborAsyncClient | None
            Harbor client to override the default client with.
        """
        # NOTE: these overrides are used mainly for testing
        if config:
            self.config = config
        if client:
            self.client = client
        self.loop = asyncio.get_event_loop()
        self.options = CommonOptions()

    @property
    def client(self) -> HarborAsyncClient:
        """Harbor async client object.

        Returns a client with bogus defaults if the client is not configured.
        """
        # NOTE: we use this pattern so users can invoke commands without
        # first having provided authentication info. Only when we try to
        # use the client, will we detect that no authentication info is provided,
        # and then we can prompt the user for it.
        # We have to keep re-using this client object, because it's directly
        # referenced by the various commands, so we have to patch it in-place
        # when we get the authentication info.
        if self._client is None:
            # Direct assignment to avoid triggering the setter
            self._client = HarborAsyncClient(
                url="http://example.com",
                username="username",
                secret="password",
            )
        return self._client

    @client.setter
    def client(self, client: HarborAsyncClient) -> None:
        self._client = client
        self._client_loaded = True

    @property
    def config(self) -> HarborCLIConfig:
        """The current program configuration.

        Returns the default config if no config is loaded.
        """
        if self._config is None:
            return HarborCLIConfig()
        return self._config

    @config.setter
    def config(self, config: HarborCLIConfig) -> None:
        self._config = config
        self._config_loaded = True

    @property
    def is_config_loaded(self) -> bool:
        """Whether or not the the config has been loaded."""
        # If we have assigned a custom config, it's loaded
        return self._config_loaded

    @property
    def is_client_loaded(self) -> bool:
        return self._client_loaded

    @property
    def console(self) -> Console:
        """Rich console object."""
        # fmt: off
        if not self._console:
            from .output.console import console # lazy load the console
            self._console = console
        return self._console
        # fmt: on

    @property
    def cache(self) -> Cache:
        """The program cache.
        Initializes the cache if it's not already initialized."""
        # fmt: off
        if self._cache is None:
            from .cache import Cache
            self._cache = Cache()
        return self._cache
        # fmt: on

    def configure_cache(self) -> None:
        """Configure the cache based on the config."""
        self.cache.ttl = self.config.cache.ttl
        self.cache.enabled = self.config.cache.enabled
        # Start the cache flushing loop
        if not self.cache._loop_running:
            self.loop.create_task(self.cache.start_flush_loop())

    def _init_client(self) -> None:
        """Configures Harbor client if it hasn't been configured yet.

        Prompts for necessary authentication info if it's missing from the config.
        """
        from .harbor.common import prompt_url
        from .harbor.common import prompt_username_secret
        from .logs import logger

        if not self.config.harbor.url:
            logger.warning("Harbor API URL missing from configuration file.")
            self.config.harbor.url = prompt_url()

        # We need one of the available auth methods to be specified
        # If not, prompt for username and password
        if not self.config.harbor.has_auth_method:
            logger.warning(
                "Harbor authentication method is missing or incomplete in configuration file."
            )
            # TODO: refactor this so we can re-use username and password
            # prompts from commands.cli.init!
            username, secret = prompt_username_secret(
                self.config.harbor.username,
                self.config.harbor.secret.get_secret_value(),
            )
            self.config.harbor.username = username
            self.config.harbor.secret = secret  # type: ignore # pydantic.SecretStr

        self.client.authenticate(**self.config.harbor.credentials)

        # Raw + validate modes
        self.client.raw = self.config.harbor.raw_mode
        self.client.validate = self.config.harbor.validate_data

        # Retry settings
        if self.client.retry is not None:
            self.client.retry.enabled = self.config.harbor.retry.enabled
            self.client.retry.max_tries = self.config.harbor.retry.max_tries
            self.client.retry.max_time = self.config.harbor.retry.max_time

        self._client_loaded = True
        # TODO: test that authentication works

    def run(
        self,
        coro: Awaitable[T],
        status: Optional[str] = None,
        no_handle: type[Exception] | tuple[type[Exception], ...] | None = None,
    ) -> T:
        """Run a coroutine in the event loop.

        Parameters
        ----------
        coro : Awaitable[T]
            The coroutine to run, which returns type T.
        status : str, optional
            The status message to display while the coroutine is running.
        no_handle : type[Exception] | tuple[type[Exception], ...] | None
            One or more Exception types to not pass to the default
            exception handler. All other exceptions will be handled.
            If None, all exceptions will be handled.

        Returns
        -------
        T
            The return value of the coroutine.

        See Also
        --------
        [harbor_cli.exceptions.handle_exception][]
        """
        # Make sure client is loaded and configured
        if not self.is_client_loaded:
            self._init_client()

        if not status:
            status = "Working..."
        if not status.endswith("..."):  # aesthetic :)
            status += "..."

        # show spinner when running a coroutine
        try:
            with self.console.status(status):
                resp = self.loop.run_until_complete(coro)
        except Exception as e:
            if no_handle and isinstance(e, no_handle):
                raise e
            # fmt: off
            from .exceptions import handle_exception
            handle_exception(e)
            # fmt: on
        return resp


_STATE = None  # type: State | None


def get_state() -> State:
    """Returns the global state object.

    Instantiates a new state object with defaults if it doesn't exist."""
    global _STATE
    if _STATE is None:
        _STATE = State()
    return _STATE
