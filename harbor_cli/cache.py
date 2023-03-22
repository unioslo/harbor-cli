from __future__ import annotations

import asyncio
import threading
import time
from typing import Any
from typing import Dict
from typing import Iterable
from typing import NamedTuple
from typing import overload
from typing import Type
from typing import TypeVar

import click

from .types import assert_type

T = TypeVar("T")


class CachedItem(NamedTuple):
    """A cached item."""

    value: Any
    expiry: float


class Cache:
    """In-memory time-based cache."""

    # A simple implementation of a time-based cache.
    # Since this is a CLI application, it makes no sense to require/support
    # Redis or something similar.

    _cache: Dict[str, CachedItem]
    _lock: threading.Lock
    _loop_running: bool = False
    enabled: bool = True
    ttl: int

    def __init__(self, ttl: int = 300) -> None:
        """Initialize the cache."""
        self.ttl = ttl
        self._cache: Dict[str, CachedItem] = {}
        self._lock = threading.Lock()

    def keys(self) -> list[str]:
        """Return the cache keys."""
        return list(self._cache.keys())

    def values(self) -> Iterable[CachedItem]:
        return self._cache.values()

    def items(self) -> Iterable[tuple[str, CachedItem]]:
        return self._cache.items()

    def _key_from_ctx(self, ctx: click.Context) -> str:
        """Get a key from a context."""
        # TODO: construct key differently for different commands
        return f"{ctx.command_path.strip()} {ctx.params} {ctx.args}"

    @overload
    def get(self, key: str | click.Context, expect_type: None = None) -> Any | None:
        ...

    @overload
    def get(self, key: str | click.Context, expect_type: Type[T] = ...) -> T | None:
        ...

    def get(
        self, key: str | click.Context, expect_type: Type[T] | None = None
    ) -> T | Any | None:
        """Get a value from the cache, or None if it doesn't exist.

        Accepts optional argument `expect_type` to signal to type checkers
        what the expected return type is.
        """
        if not self.enabled:
            return None

        if isinstance(key, click.Context):
            key = self._key_from_ctx(key)

        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item.expiry > time.time():
                    if expect_type is not None:
                        return assert_type(item.value, expect_type)
                    return item.value
                else:
                    del self._cache[key]
        return None

    def set(self, key: str | click.Context, value: Any) -> None:
        """Set a value in the cache."""
        if not self.enabled:
            return

        if isinstance(key, click.Context):
            key = self._key_from_ctx(key)
        with self._lock:
            self._cache[key] = CachedItem(value=value, expiry=time.time() + self.ttl)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()

    async def start_flush_loop(self) -> None:
        """Start a loop that finds expired entries every 5 minutes."""
        self._loop_running = True
        try:
            while self._loop_running:
                await asyncio.sleep(300)
                self._flush_expired()
        finally:
            self._loop_running = False

    def stop_flush_loop(self) -> None:
        """Stop the loop that finds expired entries."""
        self._loop_running = False

    def _flush_expired(self) -> None:
        # Copy list of keys, but otherwise operate on the original dict.
        for k in list(self._cache.keys()):
            with self._lock:
                v = self._cache[k]
                if v.expiry < time.time():
                    del self._cache[k]
