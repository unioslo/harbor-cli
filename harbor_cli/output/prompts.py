from __future__ import annotations

import math
from pathlib import Path
from typing import Any
from typing import overload
from typing import Type

from rich.prompt import FloatPrompt
from rich.prompt import IntPrompt
from rich.prompt import Prompt

from .console import err_console
from .formatting import path_link


def str_prompt(
    prompt: str,
    default: Any = ...,
    password: bool = False,
    show_default: bool = True,
    empty_ok: bool = False,
    **kwargs: Any,
) -> str:
    """Prompts the user for a string input. Optionally controls
    for empty input. Loops until a valid input is provided.

    Parameters
    ----------
    prompt : str
        Prompt to display to the user.
    default : Any, optional
        Default value to use if the user does not provide input.
        If not provided, the user will be required to provide input.
    password : bool, optional
        Whether to hide the input, by default False
    show_default : bool, optional
        Whether to show the default value, by default True
        `password=True` supercedes this option, and sets it to False.
    empty_ok : bool, optional
        Whether to allow input consisting of only whitespace, by default False

    """
    # Don't permit secrets to be shown ever
    if password:
        show_default = False

    # Notify user that a default secret will be used,
    # but don't actually show the secret
    if password and default not in (None, ..., ""):
        _add_str = " (leave empty to use existing value)"
    else:
        _add_str = ""

    inp = None

    while not inp:
        inp = Prompt.ask(
            f"{prompt}{_add_str}",
            password=password,
            show_default=show_default,
            default=default,
            **kwargs,
        )
        if empty_ok:  # nothing else to check
            break

        if not inp:
            err_console.print("Input cannot be empty.")
        elif inp.isspace() and inp != default:
            err_console.print("Input cannot solely consist of whitespace.")
        else:
            break
    return inp


def int_prompt(
    prompt: str,
    default: int | None = None,
    show_default: bool = True,
    min: int | None = None,
    max: int | None = None,
    show_range: bool = True,
    **kwargs: Any,
) -> int:
    return _number_prompt(
        IntPrompt,
        prompt,
        default=default,
        show_default=show_default,
        min=min,
        max=max,
        show_range=show_range,
        **kwargs,
    )


def float_prompt(
    prompt: str,
    default: float | None = None,
    show_default: bool = True,
    min: float | None = None,
    max: float | None = None,
    show_range: bool = True,
    **kwargs: Any,
) -> float:
    val = _number_prompt(
        FloatPrompt,
        prompt,
        default=default,
        show_default=show_default,
        min=min,
        max=max,
        show_range=show_range,
        **kwargs,
    )
    # explicit cast to float since users might pass in int as default
    # and we have no logic inside _number_prompt to handle that
    return float(val)


@overload
def _number_prompt(
    prompt_type: Type[IntPrompt],
    prompt: str,
    default: int | float | None = ...,
    show_default: bool = ...,
    min: int | float | None = ...,
    max: int | float | None = ...,
    show_range: bool = ...,
    **kwargs: Any,
) -> int:
    ...


@overload
def _number_prompt(
    prompt_type: Type[FloatPrompt],
    prompt: str,
    default: int | float | None = ...,
    show_default: bool = ...,
    min: int | float | None = ...,
    max: int | float | None = ...,
    show_range: bool = ...,
    **kwargs: Any,
) -> float:
    ...


def _number_prompt(
    prompt_type: Type[IntPrompt] | Type[FloatPrompt],
    prompt: str,
    default: int | float | None = None,
    show_default: bool = True,
    min: int | float | None = None,
    max: int | float | None = None,
    show_range: bool = True,
    **kwargs: Any,
) -> int | float:
    default_arg = ... if default is None else default

    if show_range:
        _prompt_add = ""
        if min is not None and max is not None:
            if min > max:
                raise ValueError("min must be less than or equal to max")
            _prompt_add = f"{min}<=x<={max}"
        elif min is not None:
            _prompt_add = f"x>={min}"
        elif max is not None:
            _prompt_add = f"x<={max}"
        if _prompt_add:
            prompt = f"{prompt} [yellow][{_prompt_add}][/]"

    while True:
        val = prompt_type.ask(
            prompt,
            default=default_arg,
            show_default=show_default,
            **kwargs,
        )

        # Shouldn't happen, but ask() returns DefaultType | int | float
        # so it thinks we could have an ellipsis here
        if not isinstance(val, (int, float)):
            err_console.print("Value must be a number")
            continue
        if math.isnan(val):
            err_console.print("Value can't be NaN")
            continue
        if min is not None and val < min:
            err_console.print(f"Value must be greater or equal to {min}")
            continue
        if max is not None and val > max:
            err_console.print(f"Value must be less than or equal to {max}")
            continue
        return val


def path_prompt(
    prompt: str,
    default: Any = ...,
    show_default: bool = True,
    exist_ok: bool = True,
    must_exist: bool = False,
    **kwargs: Any,
) -> Path:
    if isinstance(default, Path):
        default_arg = str(default)
    elif default is None:
        default_arg = ...  # type: ignore
    else:
        default_arg = default

    while True:
        path_str = str_prompt(
            prompt,
            default=default_arg,
            show_default=show_default,
            **kwargs,
        )
        path = Path(path_str)

        if must_exist and not path.exists():
            err_console.print(f"Path does not exist: {path_link(path)}")
        elif not exist_ok and path.exists():
            err_console.print(f"Path already exists: {path_link(path)}")
        else:
            return path
