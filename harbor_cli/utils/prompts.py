from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import HarborCLIConfig

from ..output.prompts import bool_prompt
from ..output.console import exit


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
