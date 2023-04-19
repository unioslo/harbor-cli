from __future__ import annotations

from pathlib import Path

from ..output.prompts import path_prompt
from ..output.prompts import str_prompt


def prompt_username_secret(
    default_username: str | None = None, default_secret: str | None = None
) -> tuple[str, str]:
    username = str_prompt(
        "Harbor username",
        default=default_username,
    )
    secret = str_prompt(
        "Harbor secret",
        default=default_secret,
        password=True,
    )
    return username, secret


def prompt_basicauth(default: str | None = None) -> str:
    return str_prompt(
        "Harbor Base64 Basic Auth (e.g. dXNlcjpwYXNzd29yZA==)",
        default=default,
        password=True,
    )


def prompt_credentials_file(default: Path | None = None) -> Path:
    return path_prompt(
        "Harbor credentials file (e.g. /path/to/robot.json)",
        default=default,
        show_default=True,
        must_exist=True,
        exist_ok=True,
    )


def prompt_url(default: str | None = None) -> str:
    return str_prompt(
        "Harbor API URL (e.g. https://harbor.example.com/api/v2.0)",
        default=default,
    )
