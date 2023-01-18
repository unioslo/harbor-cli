from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Any
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
from harbor_cli.output.prompts import str_prompt

# TODO: test defaults


def leading_newline() -> Iterator[str]:
    """Yields a leading newline and then no leading newline.

    This helps us test whether or not empty inputs prompts the user to
    input again.
    """
    yield "\n"
    yield ""


@pytest.mark.parametrize("leading_newline", leading_newline())
@given(st.text(min_size=1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_str_prompt(monkeypatch: MonkeyPatch, leading_newline: str, text: str) -> None:
    assume(not text.isspace())  # not testing pure whitespace
    stdin_str = leading_newline + text + "\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    # Result is always stripped of whitespace, and newline = enter
    # So anything after \n is ignored
    assert str_prompt("foo") == text.strip().split("\n")[0]


@pytest.mark.skip(reason="Flaky test in CI. Need to investigate.")
@given(st.text())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_str_prompt_empty_ok(monkeypatch: MonkeyPatch, text: str) -> None:
    stdin_str = text + "\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    # Result is always stripped of whitespace, and newline = enter
    # So anything after \n is ignored
    assert str_prompt("foo", empty_ok=True) == text.strip().split("\n")[0]


# NOTE: This is way too complicated
def test_str_prompt_looping(monkeypatch: MonkeyPatch, capsys: CaptureFixture) -> None:
    # Patches Prompt.ask to only return empty strings
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "")

    async def send_interrupt(*args: Any, **kwargs: Any) -> None:
        await asyncio.sleep(0.01)
        raise KeyboardInterrupt

    # Schedule the interrupt to be sent after 1 second
    loop = asyncio.new_event_loop()
    interrupt_task = loop.create_task(send_interrupt())

    # TODO: pass locals to thread somehow
    prompt_fut = loop.run_in_executor(None, str_prompt, "foo")

    with pytest.raises(KeyboardInterrupt):
        t = asyncio.gather(interrupt_task, prompt_fut)
        loop.run_until_complete(t)

    # FIXME: we can't read capsys from other thread
    #        how to schedule interruption without thread?

    # stdout, stderr = capsys.readouterr()
    # expect_msg = "Input cannot be empty."
    # assert expect_msg in stderr
    # assert "\n".join([expect_msg] * 2) in stderr
    # # TODO: assert that the prompt was called multiple times using pytest-mock


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
    stdin_str = leading_newline + leading_float + str(inp) + "\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    assert int_prompt("foo") == inp


@pytest.mark.parametrize("leading_newline", leading_newline())
@given(st.floats(allow_nan=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_float_prompt(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture, leading_newline: str, inp: float
) -> None:
    # so we can test that empty input prompts again
    stdin_str = leading_newline + str(inp) + "\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_str))
    assert float_prompt("foo") == inp
    if leading_newline:
        # Rich prints this message to stdout for some reason
        assert "Please enter a number" in capsys.readouterr().out


@pytest.mark.parametrize("leading_newline", leading_newline())
def test_float_prompt_nan(
    monkeypatch: MonkeyPatch, leading_newline: str, capsys: CaptureFixture
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
