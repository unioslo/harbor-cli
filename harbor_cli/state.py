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

# THIS MODULE CANNOT IMPORT FROM ANY OTHER MODULE IN THE PROJECT
# The state module should be importable by every other module in the
# project, so that it can be used as a singleton shared between all
# commands. This is necessary because the state object is not passed
# to each command, but is instead accessed via the global state variable.
# If we import from any other module, we will create a circular import problem.


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
    """Class used to manage the state of the program.

    It is used as a singleton shared between all commands.
    Unlike a context object, the state object is not passed to each
    command, but is instead accessed via the global state variable.
    """

    # Bogus defaults so we can instantiate the client before the config is loaded
    client: HarborAsyncClient
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    options: CommonOptions = CommonOptions()
    repl: bool = False
    console: Console = Console()  # the default console

    # Attributes that are lazily loaded (exposed as properties)
    _cache = None  # type: Cache | None
    _config = None  # type: HarborCLIConfig | None

    # Flags to indicate if attributes are configured (i.e. not using defaults)
    _config_loaded: bool = False
    _console_loaded: bool = False
    _client_loaded: bool = False

    def __init__(
        self,
        config: HarborCLIConfig | None = None,
        client: HarborAsyncClient | None = None,
    ) -> None:
        """Initialize the state object."""
        if config:
            self.config = config

        if client:
            self.client = client
            self._client_loaded = True
        else:
            # bogus defaults which we override when the config is loaded
            self.client = HarborAsyncClient(
                url="http://example.com",
                username="username",
                secret="password",
            )

        self.loop = asyncio.get_event_loop()
        self.options = CommonOptions()

    @property
    def cache(self) -> Cache:
        """Return the cache object."""
        # fmt: off
        if self._cache is None:
            from .cache import Cache
            self._cache = Cache()
        return self._cache
        # fmt: on

    # TODO: we could get rid of _config_loaded by returning a new default config
    # if none exists, and only write to _config if a new config is set.
    # config_loaded would then be True if _config is not None.
    @property
    def config(self) -> HarborCLIConfig:
        """Return the config object."""
        # fmt: off
        if self._config is None:  # lazy import to avoid circular imports
            from .config import HarborCLIConfig
            self._config = HarborCLIConfig()
        return self._config
        # fmt: on

    @config.setter
    def config(self, config: HarborCLIConfig) -> None:
        self._config = config
        self._config_loaded = True

    @property
    def config_loaded(self) -> bool:
        return self._config_loaded

    @property
    def console_loaded(self) -> bool:
        return self._console_loaded

    @property
    def client_loaded(self) -> bool:
        return self._client_loaded

    def configure_cache(self) -> None:
        """Configure the cache based on the config."""
        self.cache.ttl = self.config.cache.ttl
        self.cache.enabled = self.config.cache.enabled
        # Start the cache flushing loop
        self.loop.create_task(self.cache.start_flush_loop())

    def _init_console(self) -> None:
        """Import the global console object if it hasn't been imported yet.
        We do this here, so that we don't create a circular import
        between the state module and the output module."""
        # I really hate this, but due to the way the state object is
        # globally instantiated, it's difficult to conceive a way to do
        # this without creating a circular import _somewhere_.
        # I suppose we could run some sort analysis tool to figure out
        # the optimal way to structure the modules to accommodate this
        # pattern, but I'm not sure it's worth the effort (yet).
        # fmt: off
        from .output.console import console
        self.console = console
        self._console_loaded = True
        # fmt: on

    def _init_client(self) -> None:
        """Configures  Harbor client if it hasn't been configured yet.

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
            One or more Exception types to not handle.
            If None, all exceptions will be handled using the default
            exception handler.

        Returns
        -------
        T
            The return value of the coroutine.

        See Also
        --------
        [harbor_cli.exceptions.handle_exception][]
        """
        # Make sure console and client are loaded
        if not self._console_loaded:
            self._init_console()
        if not self._client_loaded:
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


state = State()
