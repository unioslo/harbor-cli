from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import HarborCLIConfig
    from ..state import State

from ..output.prompts import bool_prompt
from ..output.console import exit
from ..style import STYLE_CLI_OPTION


def delete_prompt(
    config: HarborCLIConfig,
    force: bool,
    dry_run: bool = False,
    resource: str | None = None,
    name: str | None = None,
) -> None:
    """Prompt user to confirm deletion of artifact."""
    if dry_run:
        return
    if force:
        return
    if config.general.confirm_deletion:
        resource = resource or "resource(s)"
        name = f" {name!r}" if name else ""
        message = f"Are you sure you want to delete the {resource}{name}?"
        if not bool_prompt(message, default=False):
            exit("Deletion aborted.")
    return


def check_enumeration_options(
    state: State,
    query: str | None = None,
    limit: int | None = None,
) -> None:
    if state.config.output.confirm_enumeration and not limit and not query:
        if not bool_prompt(
            f"Neither [{STYLE_CLI_OPTION}]--query[/] nor [{STYLE_CLI_OPTION}]--limit[/] is specified. "
            "This could result in a large amount of data being returned. "
            "Do you want to continue?",
            warning=True,
        ):
            exit()
