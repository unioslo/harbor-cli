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

from .cache import Cache
from .exceptions import handle_exception
from .harbor.common import prompt_url
from .harbor.common import prompt_username_secret
from .logs import logger

if TYPE_CHECKING:
    from .config import HarborCLIConfig

T = TypeVar("T")


# fmt: off
def get_default_config() -> HarborCLIConfig:
    """Lazy-import config to avoid circular imports."""
    from .config import HarborCLIConfig
    return HarborCLIConfig()
# fmt: on


def get_default_client() -> HarborAsyncClient:
    return HarborAsyncClient(
        url="http://example.com",
        username="username",
        secret="password",
    )


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

    # Initialize with defaults that will be overwritten by the CLI
    config: HarborCLIConfig

    # Bogus defaults so we can instantiate the client before the config is loaded
    client: HarborAsyncClient
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    options: CommonOptions = CommonOptions()
    repl: bool = False
    console: Console = Console()  # the default console
    cache: Cache = Cache()
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
            self.add_config(config)
        else:
            self.config = get_default_config()

        if client:
            self.add_client(client)
        else:
            self.client = get_default_client()

        self.loop = asyncio.get_event_loop()
        self.options = CommonOptions()

    @property
    def config_loaded(self) -> bool:
        """Return True if the config has been loaded."""
        return self._config_loaded

    @property
    def console_loaded(self) -> bool:
        """Return True if the console has been loaded."""
        return self._console_loaded

    @property
    def client_loaded(self) -> bool:
        """Return True if the client has been loaded."""
        return self._client_loaded

    def add_config(self, config: "HarborCLIConfig") -> None:
        """Add a config object to the state."""
        self.config = config
        self._config_loaded = True

    def add_client(self, client: HarborAsyncClient) -> None:
        """Add a client object to the state."""
        self.client = client
        self._client_loaded = True

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
        self._client_loaded = True
        # TODO: test that authenication works

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
            handle_exception(e)
        return resp


state = State()
