from __future__ import annotations

from pathlib import Path
from typing import Any

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
    for empty input.

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
        Whether to allow empty string as result, by default False.
        Set to True to allow empty string as result.

    """
    # Don't permit secrets to be shown ever
    if password:
        show_default = False

    # Notify user that a default secret will be used,
    # but don't actually show the secret
    if password and default:
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

        if not inp:
            # Default is empty string, and we allow empty input result
            if empty_ok:
                break
            else:
                err_console.print("[b]ERROR:[/] Input cannot be empty.")

    return inp


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
            err_console.print(f"[b]ERROR:[/] Path does not exist: {path_link(path)}")
        elif not exist_ok and path.exists():
            err_console.print(f"[b]ERROR:[/] Path already exists: {path_link(path)}")
        else:
            return path
