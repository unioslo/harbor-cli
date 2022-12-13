""""""
from __future__ import annotations

import typer

from . import artifact as artifact
from . import config as config
from . import gc as gc
from . import project as project
from . import system as system
from . import user as user
from . import vulnerabilities as vulnerabilities

api_commands: list[typer.Typer] = [
    project.app,
    system.app,
    artifact.app,
    user.app,
    config.app,
    gc.app,
]
