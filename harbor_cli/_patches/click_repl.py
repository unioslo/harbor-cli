"""Patches for the click_repl package."""

from __future__ import annotations

import shlex
import sys
from typing import Any
from typing import Dict
from typing import Optional

import click
import click_repl  # type: ignore
from click.exceptions import Exit as ClickExit
from click_repl import ExitReplException  # type: ignore
from click_repl import bootstrap_prompt  # type: ignore
from click_repl import dispatch_repl_commands  # type: ignore
from click_repl import handle_internal_commands  # type: ignore
from prompt_toolkit.shortcuts import prompt

from harbor_cli._patches.common import get_patcher
from harbor_cli.exceptions import handle_exception

patcher = get_patcher(f"click_repl version: {click_repl.__version__}")


def patch_exception_handling() -> None:
    """Patch click_repl's exception handling to fall back on the
    CLI's exception handlers instead of propagating them.

    Without this patch, any exceptions other than SystemExit and ClickExit
    will cause the REPL to exit. This is not desirable, as we want
    raise exceptions for control flow purposes in commands to abort them,
    but not terminate the CLi completely.

    A failed command should return to the REPL prompt instead of exiting
    the REPL.
    """

    def repl(  # noqa: C901
        old_ctx: click.Context,
        prompt_kwargs: Optional[Dict[str, Any]] = None,
        allow_system_commands: bool = True,
        allow_internal_commands: bool = True,
    ) -> Any:
        """
        Start an interactive shell. All subcommands are available in it.

        :param old_ctx: The current Click context.
        :param prompt_kwargs: Parameters passed to
            :py:func:`prompt_toolkit.shortcuts.prompt`.

        If stdin is not a TTY, no prompt will be printed, but only commands read
        from stdin.

        """
        # parent should be available, but we're not going to bother if not
        group_ctx = old_ctx.parent or old_ctx
        group = group_ctx.command
        isatty = sys.stdin.isatty()

        # Delete the REPL command from those available, as we don't want to allow
        # nesting REPLs (note: pass `None` to `pop` as we don't want to error if
        # REPL command already not present for some reason).
        repl_command_name = old_ctx.command.name
        if isinstance(group_ctx.command, click.CommandCollection):
            available_commands = {  # type: ignore
                cmd_name: cmd_obj
                for source in group_ctx.command.sources
                for cmd_name, cmd_obj in source.commands.items()  # type: ignore
            }
        else:
            available_commands = group_ctx.command.commands  # type: ignore
        available_commands.pop(repl_command_name, None)  # type: ignore

        prompt_kwargs = bootstrap_prompt(prompt_kwargs, group)

        if isatty:

            def get_command():
                return prompt(**prompt_kwargs)

        else:
            get_command = sys.stdin.readline

        while True:
            try:
                command = get_command()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            if not command:
                if isatty:
                    continue
                else:
                    break

            if allow_system_commands and dispatch_repl_commands(command):
                continue

            if allow_internal_commands:
                try:
                    result = handle_internal_commands(command)  # type: ignore
                    if isinstance(result, str):
                        click.echo(result)
                        continue
                except ExitReplException:
                    break

            try:
                args = shlex.split(command)
            except ValueError as e:
                click.echo(f"{type(e).__name__}: {e}")
                continue

            try:
                with group.make_context(None, args, parent=group_ctx) as ctx:
                    group.invoke(ctx)
                    ctx.exit()
            except click.ClickException as e:
                e.show()
            except ClickExit:
                pass
            except SystemExit:
                pass
            except ExitReplException:
                break
            # PATCH: Patched to handle zabbix-cli exceptions
            except Exception as e:
                try:
                    handle_exception(e)  # this could be dangerous? Infinite looping?
                except SystemExit:
                    pass
            # PATCH: Patched to continue on keyboard interrupt
            except KeyboardInterrupt:
                from harbor_cli.output.console import err_console

                # User likely pressed Ctrl+C during a prompt or when a spinner
                # was active. Ensure message is printed on a new line.
                # TODO: determine if last char in terminal was newline somehow! Can we?
                err_console.print("\n[red]Aborted.[/]")
                pass

    with patcher("click_repl.repl"):
        click_repl.repl = repl


def patch() -> None:
    """Apply all patches."""
    patch_exception_handling()
