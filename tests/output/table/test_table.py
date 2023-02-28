from __future__ import annotations

from typing import Any
from typing import TypeVar

import pytest
import rich
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel

from ..._strategies import COMPACT_TABLE_MODELS
from harbor_cli.output.table import BuiltinTypeException
from harbor_cli.output.table import EmptySequenceError
from harbor_cli.output.table import get_renderable

T = TypeVar("T", bound=BaseModel)


@given(st.one_of(COMPACT_TABLE_MODELS))
def test_get_renderable(obj: BaseModel) -> None:
    renderable = get_renderable(obj)
    assert renderable is not None
    # Check that we can print it without errors
    rich.print(renderable)


@given(st.one_of(COMPACT_TABLE_MODELS))
def test_get_renderable_as_sequence(model: BaseModel | list[BaseModel]) -> None:
    assume(isinstance(model, list) and len(model) > 0)
    renderable = get_renderable(model[0])  # type: ignore
    assert renderable is not None


def test_get_renderable_empty_sequence() -> None:
    with pytest.raises(EmptySequenceError):
        get_renderable([])


@pytest.mark.parametrize("obj", [1, "str", object(), dict()])
@pytest.mark.parametrize("as_sequence", [True, False])
def test_get_renderable_builtin(obj: Any, as_sequence: bool) -> None:
    if as_sequence:
        obj = [obj]
        with pytest.raises(NotImplementedError):
            get_renderable(obj)
    else:
        with pytest.raises(BuiltinTypeException):
            get_renderable(obj)


def test_get_renderable_list_of_list() -> None:
    with pytest.raises(NotImplementedError):
        get_renderable([[]])  # type: ignore
