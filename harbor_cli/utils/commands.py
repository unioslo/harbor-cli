from __future__ import annotations

import click
import typer

from ..models import CommandSummary


def get_parent_ctx(
    ctx: typer.Context | click.core.Context,
) -> typer.Context | click.core.Context:
    """Get the top-level parent context of a context."""
    if ctx.parent is None:
        return ctx
    return get_parent_ctx(ctx.parent)


def get_command_help(command: typer.models.CommandInfo) -> str:
    """Get the help text of a command."""
    if command.help:
        return command.help
    if command.callback and command.callback.__doc__:
        return command.callback.__doc__.strip().splitlines()[0]
    return ""


def get_app_commands(
    app: typer.Typer, cmds: list[CommandSummary] | None = None, current: str = ""
) -> list[CommandSummary]:
    if cmds is None:
        cmds = []

    # When we have commands, we don't need to go deeper and are done.
    # We can now construct the CommandSummary objects.
    for command in app.registered_commands:
        if not command.name:
            continue
        if current:
            name = f"{current} {command.name}"
        else:
            name = command.name
        cmds.append(CommandSummary(name=name, help=get_command_help(command)))

    # If we have subcommands, we need to go deeper.
    for group in app.registered_groups:
        if not group.typer_instance:
            continue
        t = group.typer_instance
        if current == "":
            new_current = t.info.name or ""
        else:
            new_current = f"{current} {t.info.name or ''}"
        get_app_commands(t, cmds, current=new_current)

    return sorted(cmds, key=lambda x: x.name)
