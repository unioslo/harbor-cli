from __future__ import annotations

import io

import yaml
from common import DATA_PATH
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
        if not group.typer_instance:
            continue
        t = group.typer_instance
        cmds[t.info.name or str(group)] = get_commands(t)
    return cmds


def render_commandlist(
    cmds: dict[str, dict], writer: io.StringIO | None = None, current: str = ""
) -> io.StringIO:
    """Renders a command list as a tree. Iterates recursively to print
    all commands and subcommands. Passes the current command to the next
    iteration to build the full command path.

    Uses a StringIO object to write to, which is returned at the end.
    """
    if writer is None:
        writer = io.StringIO(newline="\n")
    cmds = dict(sorted(cmds.items()))
    for cmd, subcmds in cmds.items():
        to_write = cmd
        if current:
            to_write = current + " " + cmd
        if current:
            writer.write(to_write + "\n")
        render_commandlist(subcmds, writer=writer, current=to_write)
    return writer


if __name__ == "__main__":
    commands = get_commands(app)
    w = render_commandlist(commands)
    value = w.getvalue()

    with open(DATA_PATH / "commands.txt", "w") as f:
        f.write(value)

    with open(DATA_PATH / "commands.yaml", "w") as f:
        yaml.dump(value.split("\n"), f, sort_keys=False)
