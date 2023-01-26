from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Type

import pytest
import typer
from pydantic import BaseModel

from harbor_cli.utils.args import create_updated_model
from harbor_cli.utils.args import model_params_from_ctx
from harbor_cli.utils.args import parse_commalist
from harbor_cli.utils.args import parse_key_value_args


class Model(BaseModel):
    a: str
    b: Optional[str]
    c: int
    d: Optional[int]
    e: bool
    f: Optional[bool]
    foo: str = "foo"


class ModelUpdateReq(BaseModel):
    a: Optional[str]
    b: Optional[str]
    c: Optional[int]
    d: Optional[int]
    e: Optional[bool]
    f: Optional[bool]
    bar: str = "bar"


@pytest.mark.parametrize("b", [None, "b"])
def test_model_params_from_ctx(mock_ctx: typer.Context, b: Optional[str]) -> None:

    mock_ctx.params = {
        "a": "a-updated",
        "b": b,
        "c": 11,
        "e": False,
        "foo": "foo-updated",
        "bar": "bar-updated",
    }
    params = model_params_from_ctx(mock_ctx, Model)
    # kinda primitive but whatever
    if b is None:
        assert params == {
            "a": "a-updated",
            "c": 11,
            "e": False,
            "foo": "foo-updated",
        }
    else:
        assert params == {
            "a": "a-updated",
            "b": "b",
            "c": 11,
            "e": False,
            "foo": "foo-updated",
        }


def test_create_updated_model(mock_ctx: typer.Context) -> None:
    # The model we retrieve from the API (GET /<resource>)
    model = Model(a="a", b="b", c=1, d=2, e=True, f=False)

    # The params we get from the context (CLI)
    mock_ctx.params = {
        "a": "a-updated",
        "b": "b-updated",
        "c": 11,
        "e": False,
        "foo": "foo-updated",
        "bar": "bar-updated",
    }

    # Create the updated model combining the two
    updated_model = create_updated_model(model, ModelUpdateReq, mock_ctx)
    assert updated_model == ModelUpdateReq(
        a="a-updated",
        b="b-updated",
        c=11,
        d=2,
        e=False,
        f=False,
        bar="bar-updated",
    )

    # Test with the "API" model as well
    updated_model_base = create_updated_model(model, Model, mock_ctx)
    assert updated_model_base == Model(
        a="a-updated",
        b="b-updated",
        c=11,
        d=2,
        e=False,
        f=False,
        foo="foo-updated",
    )


@pytest.mark.parametrize(
    "arg,expected",
    [
        ([], []),
        (["foo"], ["foo"]),
        (["foo,bar"], ["foo", "bar"]),
        (["foo,bar", "baz"], ["foo", "bar", "baz"]),
        (["foo,bar", "baz,qux"], ["foo", "bar", "baz", "qux"]),
    ],
)
def test_parse_commalist(arg: list[str], expected: list[str]) -> None:
    assert parse_commalist(arg) == expected


@pytest.mark.parametrize(
    "arg,expected",
    [
        ([], {}),
        (["foo=bar"], {"foo": "bar"}),
        (["foo=bar", "baz=qux"], {"foo": "bar", "baz": "qux"}),
        (
            ["foo=bar", "baz=qux", "quux=quuz"],
            {"foo": "bar", "baz": "qux", "quux": "quuz"},
        ),
    ],
)
def test_parse_key_value_arg(arg: list[str], expected: dict[str, str]) -> None:
    assert parse_key_value_args(arg) == expected


@pytest.mark.parametrize(
    "arg,expected,raises,exception",
    [
        # Valid
        ([], {}, False, None),
        (["foo=bar"], {"foo": "bar"}, False, None),
        (["foo=bar", "baz=qux"], {"foo": "bar", "baz": "qux"}, False, None),
        (
            ["foo=bar", "spam=grok", "baz=qux"],
            {"foo": "bar", "spam": "grok", "baz": "qux"},
            False,
            None,
        ),
        (
            ["foo=bar,spam=grok", "baz=qux"],
            {"foo": "bar", "spam": "grok", "baz": "qux"},
            False,
            None,
        ),
        (
            ["foo=bar", "spam=grok", "baz=qux", "idk=lol"],
            {"foo": "bar", "spam": "grok", "baz": "qux", "idk": "lol"},
            False,
            None,
        ),
        (
            ["foo=bar,spam=grok", "baz=qux,idk=lol"],
            {"foo": "bar", "spam": "grok", "baz": "qux", "idk": "lol"},
            False,
            None,
        ),
        # Invalid
        (["foo"], {"foo": None}, True, typer.BadParameter),
        (["foo=bar", "baz"], {"foo": "bar", "baz": None}, True, typer.BadParameter),
        (
            ["foo=bar", "baz=qux", "quux"],
            {"foo": "bar", "baz": "qux", "quux": None},
            True,
            typer.BadParameter,
        ),
    ],
)
def test_parse_key_value_arg_with_comma(
    arg: List[str],
    expected: Dict[str, str],
    raises: bool,
    exception: Optional[Type[Exception]],
) -> None:
    if raises and exception is not None:
        with pytest.raises(exception):
            args = parse_commalist(arg)
            parse_key_value_args(args)
    else:
        args = parse_commalist(arg)
        assert parse_key_value_args(args) == expected
