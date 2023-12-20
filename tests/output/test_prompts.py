from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterator

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st
from pytest import CaptureFixture
from pytest import MonkeyPatch

from harbor_cli.output.prompts import float_prompt
from harbor_cli.output.prompts import int_prompt
from harbor_cli.output.prompts import path_prompt
from harbor_cli.output.prompts import prompt_msg
from harbor_cli.output.prompts import str_prompt
from harbor_cli.style.color import green
from harbor_cli.style.style import Icon

# TODO: test defaults


def test_input_mocking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test input with built-in input() instead of our input functions."""
    s1 = "hello, world!"
    s2 = "goodbye, world!"
    sep = os.linesep

    # Blank line, then two lines with strings
    stdin_str = sep + s1 + sep + s2 + sep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str, newline=sep))

    # We first get a prompt where we are just expected to press enter
    # Then we get two prompts where we are expected to enter a string
    input("Continue?")  # first prompt
    assert input("Greeting") == s1  # second prompt
    assert input("Farewell") == s2  # third prompt


def leading_newline() -> Iterator[str]:
    """Yields a leading newline and then no leading newline.

    This helps us test whether or not empty inputs prompts the user to
    input again.
    """
    yield os.linesep
    yield ""


@pytest.mark.timeout(1)
@pytest.mark.parametrize("leading_newline", leading_newline())
@given(st.text(min_size=1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_str_prompt(monkeypatch: MonkeyPatch, leading_newline: str, text: str) -> None:
    assume(not text.isspace())  # not testing pure whitespace
    stdin_str = leading_newline + text + os.linesep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    # Result is always stripped of whitespace, and newline = enter
    # So anything after \n is discarded.
    # Also, if hypothesis generates something like '0\r\n0', then
    # we need to strip the \r as well, since that's also discarded.
    expect = text.strip().split(os.linesep)[0].strip()
    assert str_prompt("foo") == expect


@pytest.mark.timeout(1)
@given(st.text())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_str_prompt_empty_ok(monkeypatch: MonkeyPatch, text: str) -> None:
    stdin_str = text + os.linesep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    # Result is always stripped of whitespace, and newline = enter
    # So anything after \n is ignored
    assert str_prompt("foo", empty_ok=True) == text.split(os.linesep)[0].strip()


@pytest.mark.timeout(1)
@pytest.mark.parametrize("leading_newline", leading_newline())
@pytest.mark.parametrize("leading_float", ["", "3.14159265358979\n"])
@given(st.integers())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_int_prompt(
    monkeypatch: MonkeyPatch,
    # Leading newline prompts for new input
    leading_newline: str,
    # Floating point numbers are invalid, and will prompt for new input
    leading_float: str,
    inp: int,
) -> None:
    stdin_str = leading_newline + leading_float + str(inp) + os.linesep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    assert int_prompt("foo") == inp


@pytest.mark.timeout(1)
@pytest.mark.parametrize("leading_newline", leading_newline())
@given(st.floats(allow_nan=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_float_prompt(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture, leading_newline: str, inp: float
) -> None:
    # so we can test that empty input prompts again
    stdin_str = leading_newline + str(inp) + os.linesep
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    assert float_prompt("foo") == inp
    if leading_newline:
        # Rich prints this message to stdout for some reason
        assert "Please enter a number" in capsys.readouterr().out


@pytest.mark.timeout(1)
@pytest.mark.parametrize("leading_newline", leading_newline())
def test_float_prompt_nan(
    monkeypatch: MonkeyPatch,
    leading_newline: str,
    capsys: CaptureFixture,
) -> None:
    # if we give it a nan, it will prompt for new input
    # so we need to give it a valid input after that
    stdin_str = leading_newline + "nan\n" + "0.0\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    assert float_prompt("foo") == 0.0
    stdout, stderr = capsys.readouterr()
    assert "NaN" in stderr
    if leading_newline:
        # Rich prints this message to stdout for some reason
        assert "Please enter a number" in stdout


def test_path_prompt(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    p = tmp_path / "test.txt"
    p = p.resolve().absolute()
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{p}\n"))
    assert path_prompt("foo") == p


@pytest.mark.parametrize(
    "inp, expected",
    [
        (("foo",), "foo"),
        (("foo", "bar"), "foo bar"),
        (("foo", "bar", "baz", "gux"), "foo bar baz gux"),
        (("foo", ""), "foo"),
        (("foo", None), "foo"),
    ],
)
def test_prompt_msg(inp: tuple[str, ...], expected: str) -> None:
    assert prompt_msg(*inp) == f"[bold]{green(Icon.PROMPT)} {expected}[/bold]"


@pytest.mark.timeout(1)
@pytest.mark.parametrize(
    "prompt_func",
    [
        str_prompt,
        int_prompt,
        float_prompt,
        path_prompt,
    ],
)
def test_no_headless_decorator(
    monkeypatch_env, caplog: pytest.LogCaptureFixture, prompt_func: Callable[[Any], Any]
) -> None:
    """Test that the no_headless decorator causes ."""
    with pytest.raises(SystemExit):
        prompt_func("This should fail")
    assert "Headless session" in caplog.text
