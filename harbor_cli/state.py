from __future__ import annotations

import asyncio
from typing import Awaitable
from typing import TypeVar

from harborapi import HarborAsyncClient
from harborapi.exceptions import StatusError
from pydantic import BaseModel
from pydantic import Field

from .config import HarborCLIConfig
from .exceptions import handle_status_error

T = TypeVar("T")


class State(BaseModel):
    """Class used to manage the state of the program.

    It is used as a singleton shared between all commands.
    Unlike a context object, the state object is not passed to each
    command, but is instead accessed via the global state variable.
    """

    config: HarborCLIConfig = Field(default_factory=HarborCLIConfig)
    client: HarborAsyncClient = None  # type: ignore # will be patched by the callback
    verbose: bool = False
    loop: asyncio.AbstractEventLoop = Field(default_factory=asyncio.get_event_loop)

    class Config:
        keep_untouched = (asyncio.AbstractEventLoop,)
        arbitrary_types_allowed = True  # HarborAsyncClient
        validate_assignments = True
        extra = "allow"

    def run(self, coro: Awaitable[T]) -> T:
        """Run a coroutine in the event loop."""
        try:
            resp = self.loop.run_until_complete(coro)
        except StatusError as e:
            handle_status_error(e)
        return resp


state = State()
