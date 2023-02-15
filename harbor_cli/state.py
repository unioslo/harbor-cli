from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:
    from rich.console import Console

from harborapi import HarborAsyncClient
from pydantic import BaseModel

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

    class Config:
        extra = "allow"


class State:
    """Class used to manage the state of the program.

    It is used as a singleton shared between all commands.
    Unlike a context object, the state object is not passed to each
    command, but is instead accessed via the global state variable.
    """

    config: HarborCLIConfig
    client: HarborAsyncClient
    loop: asyncio.AbstractEventLoop
    options: CommonOptions
    repl: bool = False
    config_loaded: bool = False
    console: Optional[Console]

    def __init__(self) -> None:
        """Initialize the state object."""
        self.config = HarborCLIConfig()
        self.client = None  # type: ignore # will be patched by init_state
        self.loop = asyncio.get_event_loop()
        self.options = CommonOptions()
        self.console = None

    def add_config(self, config: "HarborCLIConfig") -> None:
        """Add a config object to the state."""
        self.config = config
        self.config_loaded = True

    def add_client(self, client: HarborAsyncClient) -> None:
        """Add a client object to the state."""
        self.client = client

    def _init_console(self) -> None:
        """Import the console object if it hasn't been imported yet.
        We do this here, so that we don't create a circular import
        between the state module and the output module."""
        # fmt: off
        from .output.console import console
        self.console = console
        # fmt: on

    def run(
        self,
        coro: Awaitable[T],
        status: Optional[str] = None,
        no_handle: Type[Exception] | Tuple[Type[Exception], ...] | None = None,
    ) -> T:
        """Run a coroutine in the event loop.

        Parameters
        ----------
        coro : Awaitable[T]
            The coroutine to run.
        no_handle : Type[Exception] | Tuple[Type[Exception], ...]
            A single exception type or a tuple of exception types that
            should not be passed to the default exception handler.
            Exceptions of this type will be raised as-is.
        """
        if self.console is None:
            self._init_console()
            assert self.console is not None

        if not status:
            status = "Working..."
        if not status.endswith("..."):  # aesthetic :)
            status += "..."

        # show spinner when running a coroutine
        with self.console.status(status):
            resp = self.loop.run_until_complete(coro)
        return resp


state = State()
