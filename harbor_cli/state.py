from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypeVar

from harborapi import HarborAsyncClient
from pydantic import BaseModel
from pydantic import ConfigDict
from rich.console import Console

# This module generally shouldn't import from other local modules
# because it's widely used throughout the application, and we don't want
# to create circular import issues. It sucks, but it's the way it is.

if TYPE_CHECKING:
    from .config import HarborCLIConfig


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
    model_config = ConfigDict(extra="allow")


class State:
    """Object that encapsulates the current state of the application.
    Holds the current configuration, harbor client, and other stateful objects
    that we want access to inside commands.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    options: CommonOptions = CommonOptions()
    loop: asyncio.AbstractEventLoop
    repl: bool = False

    # Attributes (exposed as properties)
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
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
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
        # when we receive new authentication info.
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

        Returns a default config if no config is loaded.
        The default config is just a placeholder that is expected
        to be replaced with a custom config loaded from a config file.
        """
        # fmt: off
        if self._config is None:
            from .config import HarborCLIConfig
            self._config = HarborCLIConfig()
        return self._config
        # fmt: on

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
            from .output.console import console
            self._console = console
        return self._console
        # fmt: on

    def authenticate_harbor(self) -> None:
        self.client.authenticate(**self.config.harbor.credentials)

    def _init_client(self) -> None:
        """Configures Harbor client if it hasn't been configured yet.

        Prompts for necessary authentication info if it's missing from the config.
        """
        from .harbor.common import prompt_url
        from .harbor.common import prompt_username_secret
        from .style.style import render_cli_command
        from .style.style import render_cli_option
        from .style.style import render_cli_value
        from .output.console import warning

        if not self.config.harbor.url:
            warning("Harbor API URL missing from configuration file.")
            self.config.harbor.url = prompt_url()

        # We need one of the available auth methods to be specified
        # If not, prompt for username and password
        if not self.config.harbor.has_auth_method:
            warning(
                "Harbor authentication method is missing or incomplete in configuration file."
            )
            username, secret = prompt_username_secret(self.config.harbor.username, "")
            self.config.harbor.username = username
            self.config.harbor.secret = secret  # type: ignore # pydantic.SecretStr
            warning(
                "Authentication info updated. "
                f"Run {render_cli_command('harbor init')} to configure it permanently. "
                f"Suppress this warning by setting {render_cli_option('general.warnings')} to {render_cli_value('false')}."
            )

        self.authenticate_harbor()

        # Raw + validate modes
        self.client.raw = self.config.harbor.raw_mode
        self.client.validate = self.config.harbor.validate_data

        # Retry settings
        if self.client.retry is not None:
            self.client.retry.enabled = self.config.harbor.retry.enabled
            self.client.retry.max_tries = self.config.harbor.retry.max_tries
            self.client.retry.max_time = self.config.harbor.retry.max_time

        self._client_loaded = True

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
        else:
            self.authenticate_harbor()  # ensure we use newest credentials

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


def get_state() -> State:
    """Returns the global state object.

    Instantiates a new state object with defaults if it doesn't exist."""
    return State()
