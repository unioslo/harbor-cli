""""""
from __future__ import annotations

import typer

from . import artifact as artifact
from . import auditlog as auditlog
from . import cve_allowlist as cve_allowlist
from . import gc as gc
from . import harbor_config as harbor_config
from . import ldap as ldap
from . import project as project
from . import quotas as quotas
from . import registry as registry
from . import replication as replication
from . import repository as repository
from . import retention as retention
from . import scan as scan
from . import scanall as scanall
from . import scanner as scanner
from . import search as search  # no subcommands
from . import system as system
from . import user as user
from . import usergroup as usergroup
from . import webhook as webhook

api_commands: list[typer.Typer] = [
    artifact.app,
    auditlog.app,
    harbor_config.app,
    cve_allowlist.app,
    gc.app,
    ldap.app,
    project.app,
    quotas.app,
    registry.app,
    replication.app,
    repository.app,
    retention.app,
    scan.app,
    scanall.app,
    scanner.app,
    system.app,
    user.app,
    usergroup.app,
    webhook.app,
]
