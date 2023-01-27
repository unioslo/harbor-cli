from __future__ import annotations

from typing import Any
from typing import Type

import pytest
import rich
from pydantic import BaseModel
from pydantic import ValidationError

from harbor_cli.output.table import BuiltinTypeException
from harbor_cli.output.table import EmptySequenceError
from harbor_cli.output.table import get_renderable
from harbor_cli.output.table import RENDER_FUNCTIONS


@pytest.mark.parametrize("model_type", RENDER_FUNCTIONS.keys())
def test_get_renderable(model_type: Type[BaseModel]) -> None:
    try:
        obj = model_type()
    except ValidationError:
        pytest.skip(
            f"Cannot instantiate {model_type.__name__} instance with no arguments."
        )
    renderable = get_renderable(obj)
    assert renderable is not None
    # Check that we can print it without errors
    rich.print(renderable)


@pytest.mark.parametrize("model_type", RENDER_FUNCTIONS.keys())
def test_get_renderable_as_sequence(model_type: Type[BaseModel]) -> None:
    try:
        obj = model_type()
    except ValidationError:
        pytest.skip(
            f"Cannot instantiate {model_type.__name__} instance with no arguments."
        )
    renderable_single = get_renderable([obj])
    assert renderable_single is not None
    rich.print(renderable_single)
    renderable_multi = get_renderable([obj, obj])
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
        get_renderable([[]])
