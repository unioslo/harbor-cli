from __future__ import annotations

from typing import Any
from typing import TypeVar

import pytest
import rich
from hypothesis import given
from pydantic import BaseModel

from ..._strategies import COMPACT_TABLE_MODELS
from harbor_cli.output.table import BuiltinTypeException
from harbor_cli.output.table import EmptySequenceError
from harbor_cli.output.table import get_renderable

T = TypeVar("T", bound=BaseModel)


@given(COMPACT_TABLE_MODELS)
def test_get_renderable(obj: BaseModel) -> None:
    renderable = get_renderable(obj)
    assert renderable is not None
    # Check that we can print it without errors
    rich.print(renderable)


@given(COMPACT_TABLE_MODELS)
def test_get_renderable_as_sequence(model: BaseModel) -> None:
    renderable_single = get_renderable([model])
    assert renderable_single is not None
    rich.print(renderable_single)
    renderable_multi = get_renderable([model, model])
    assert renderable_multi is not None
    rich.print(renderable_multi)


def test_get_renderable_empty_sequence() -> None:
    with pytest.raises(EmptySequenceError):
        get_renderable([])


@pytest.mark.parametrize("obj", [1, "str", object(), dict()])
@pytest.mark.parametrize("as_sequence", [True, False])
def test_get_renderable_builtin(obj: Any, as_sequence: bool) -> None:
    if as_sequence:
        obj = [obj]
    with pytest.raises(BuiltinTypeException):
        get_renderable(obj)


def test_get_renderable_list_of_list() -> None:
    with pytest.raises(BuiltinTypeException):
        get_renderable([[]])  # type: ignore
