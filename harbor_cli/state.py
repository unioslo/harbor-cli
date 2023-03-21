from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable
from typing import Optional
from typing import TypeVar

from harborapi import HarborAsyncClient
from pydantic import BaseModel
from rich.console import Console

from .cache import Cache
from .config import HarborCLIConfig
from .exceptions import handle_exception

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

    # Initialize with defaults that will be overwritten by the CLI
    config: HarborCLIConfig = HarborCLIConfig()

    # Bogus defaults so we can instantiate the client before the config is loaded
    client: HarborAsyncClient = HarborAsyncClient(
        url="http://example.com",
        username="username",
        secret="password",
    )
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    options: CommonOptions = CommonOptions()
    repl: bool = False
    console: Console = Console()  # the default console
    cache: Cache = Cache()
    _config_loaded: bool = False
    _console_loaded: bool = False
    _client_loaded: bool = False

    def __init__(self) -> None:
        """Initialize the state object."""
        self.config = HarborCLIConfig()
        self.client = None  # type: ignore # will be patched by init_state
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

    def configure_cache(self) -> None:
        """Configure the cache based on the config."""
        self.cache.ttl = self.config.cache.ttl
        self.cache.enabled = self.config.cache.enabled
        # Start the cache flushing loop
        self.loop.create_task(self.cache.start_flush_loop())

    def _init_console(self) -> None:
        """Import the console object if it hasn't been imported yet.
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
        if not self._console_loaded:
            self._init_console()

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
