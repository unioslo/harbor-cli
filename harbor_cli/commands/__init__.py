from __future__ import annotations

import typer

from . import artifact as artifact
from . import init as init
from . import project as project
from . import sample_config as sample_config
from . import system as system
from . import vulnerabilities as vulnerabilities

command_groups: list[typer.Typer] = [
    project.app,
    system.app,
    artifact.app,
]
