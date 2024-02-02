from __future__ import annotations

import asyncio
from functools import cached_property
from pathlib import Path
from typing import Coroutine
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
    from logging import Logger


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
            cls._initialized = False
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
        if self._initialized:  # prevent __init__ from running more than once
            return

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

        self._initialized = True

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

    @cached_property
    def logger(self) -> Logger:
        """Logger object."""
        from .logs import logger

        return logger

    def authenticate_harbor(self) -> None:
        self.client.authenticate(**self.config.harbor.credentials)

    def _init_client(self) -> None:
        """Configures Harbor client if it hasn't been configured yet.

        Prompts for necessary authentication info if it's missing from the config.
        """
        from .harbor.common import prompt_url
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
            self.config.harbor.set_username_secret(
                current_username=self.config.harbor.username,
                current_secret=self.config.harbor.secret_value,
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

    def try_load_config(self, config_file: Optional[Path], create: bool = True) -> None:
        """Attempts to load the config given a config file path.
        Assigns the loaded config to the state object.

        Parameters
        ----------
        config_file : Optional[Path]
            The path to the config file.
        create : bool, optional
            Whether to create a new config file if one is not found, by default True
        """
        from harbor_cli.output.console import info
        from harbor_cli.output.console import error
        from harbor_cli.output.console import exit_err
        from harbor_cli.output.formatting.path import path_link
        from harbor_cli.commands.cli.init import run_config_wizard
        from harbor_cli.exceptions import ConfigError
        from harbor_cli.config import HarborCLIConfig

        # Don't load the config if it's already loaded (e.g. in REPL)
        if not self.is_config_loaded:
            try:
                conf = HarborCLIConfig.from_file(config_file)
            except FileNotFoundError:
                if not create:
                    return
                # Create a new config file and run wizard
                info("Config file not found. Creating new config file.")
                conf = HarborCLIConfig.from_file(config_file, create=create)
                if conf.config_file is None:
                    exit_err("Unable to create config file.")
                info(f"Created config file: {path_link(conf.config_file)}")
                info("Running configuration wizard...")
                conf = run_config_wizard(conf.config_file)
            except ConfigError as e:
                error(f"Unable to load config: {str(e)}", exc_info=True)
                return

            self.config = conf

    def check_keyring_available(self) -> None:
        """Checks if the keyring is available if it's enabled in the config file.

        Important to call this method BEFORE saving a snapshot of the config!
        Otherwise, we risk enabling and disabling the keyring over and over again.
        """

        if self.config.harbor.keyring:
            from harbor_cli.utils.keyring import keyring_supported
            from harbor_cli.output.console import warning

            if not keyring_supported():
                warning(
                    "Keyring is not available on this platform. Set [i default]keyring = false[/] in config to suppress this warning."
                )
                self.config.harbor.keyring = False

    def run(
        self,
        coro: Coroutine[None, None, T],
        status: Optional[str] = None,
        no_handle: type[Exception] | tuple[type[Exception], ...] | None = None,
    ) -> T:
        """Run a coroutine in the event loop.

        Parameters
        ----------
        coro : Coroutine[None, None, T]
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
        try:
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
        finally:
            # Close coro in case we never got to run it
            # Unawaited coros emit warnings which we ideally want to know about
            # But if we error before getting to run it, we don't need a warning
            try:
                coro.close()
            except Exception:
                self.logger.debug("Failed to close coroutine.", exc_info=True)
                pass


def get_state() -> State:
    """Returns the global state object.

    Instantiates a new state object with defaults if it doesn't exist."""
    return State()
