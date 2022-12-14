""""""
from __future__ import annotations

import typer

from . import artifact as artifact
from . import auditlog as auditlog
from . import config as config
from . import gc as gc
from . import project as project
from . import scan as scan
from . import scanall as scanall
from . import scanner as scanner
from . import system as system
from . import user as user
from . import vulnerabilities as vulnerabilities

api_commands: list[typer.Typer] = [
    artifact.app,
    auditlog.app,
    config.app,
    gc.app,
    project.app,
    scan.app,
    scanall.app,
    scanner.app,
    system.app,
    user.app,
]
