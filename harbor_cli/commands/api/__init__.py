""""""
from __future__ import annotations

import typer

from . import artifacts as artifacts
from . import project as project
from . import system as system
from . import users as users
from . import vulnerabilities as vulnerabilities

api_commands: list[typer.Typer] = [
    project.app,
    system.app,
    artifacts.app,
    users.app,
]
