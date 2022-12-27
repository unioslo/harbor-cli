from __future__ import annotations

from typer import Typer

from harbor_cli.main import app


def get_commands(typer_instance: Typer) -> dict[str, dict]:
    """Returns the names of all commands as a dict of dicts,
    iterating recursively until all subcommands have been found.

    Keys are command names, values are dicts of subcommands.

    Example
    -------
    >>> get_commands(app)
    cmd = {'artifacts': {'list': {}, 'tag': {'list': {}, 'add': {}, 'delete': {}}, ...}, ...}
    """
    cmds = {}  # type: dict[str, dict]
    for command in typer_instance.registered_commands:
        cmds[command.name or str(command)] = {}
    for group in typer_instance.registered_groups:
        # cmds[group.name] = get_commands(group.typer_instance)
        if not group.typer_instance:
            continue
        t = group.typer_instance
        cmds[t.info.name or str(group)] = get_commands(t)
    return cmds


def render_commandlist(cmds: dict[str, dict], indent: int = 2, _indentlvl: int = 0):
    """Renders a commandlist as a tree."""
    cmds = dict(sorted(cmds.items()))
    for cmd, subcmds in cmds.items():
        print(" " * _indentlvl + cmd)
        render_commandlist(subcmds, indent=indent, _indentlvl=_indentlvl + indent)


commands = get_commands(app)

render_commandlist(commands, indent=2)
