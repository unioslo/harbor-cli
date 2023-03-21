from __future__ import annotations

from time import sleep
from typing import Any
from typing import List

import click
import pytest

from harbor_cli.cache import Cache


def test_cache_str_val_str_key() -> None:
    cache = Cache()
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"
    assert cache.get("foo", str) == "bar"
    assert cache.get("foo", Any) == "bar"

    with pytest.raises(TypeError):
        cache.get("foo", int)


def test_cache_list_val_str_key() -> None:
    cache = Cache()
    cache.set("foo", ["bar"])
    assert cache.get("foo") == ["bar"]
    assert cache.get("foo", list) == ["bar"]
    assert cache.get("foo", List) == ["bar"]
    assert cache.get("foo", List[str]) == ["bar"]
    assert cache.get("foo", List[Any]) == ["bar"]

    with pytest.raises(TypeError):
        assert cache.get("foo", List[int]) == ["bar"]


def test_cache_str_val_ctx_key() -> None:
    cache = Cache()

    ctx = click.Context(click.Command("foo"))
    ctx.params = {"query": "bar"}
    ctx.info_name = "get foo"

    cache.set(ctx, "bar")
    assert cache.get(ctx) == "bar"
    assert cache.get(ctx, str) == "bar"
    assert cache.get(ctx, Any) == "bar"

    with pytest.raises(TypeError):
        cache.get(ctx, int)


def test_cache_list_val_ctx_key() -> None:
    cache = Cache()

    ctx = click.Context(click.Command("foo"))
    ctx.params = {"query": "bar"}
    ctx.info_name = "get foo"

    cache.set(ctx, "bar")
    assert cache.get(ctx, str) == "bar"
    assert cache.get(ctx, Any) == "bar"

    # Test with a list of ints (overwriting the previous value)
    cache.set(ctx, [1234])
    assert cache.get(ctx, List[int]) == [1234]

    with pytest.raises(TypeError):
        cache.get(ctx, int)


def test_cache_ttl() -> None:
    cache = Cache(ttl=1)

    cache.set("foo", "bar")
    sleep(1.1)  # ttl + 100ms
    assert cache.get("foo") is None
