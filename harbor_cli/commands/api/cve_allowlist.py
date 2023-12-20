from __future__ import annotations

from typing import List

import typer
from harborapi.models.models import CVEAllowlist
from harborapi.models.models import CVEAllowlistItem

from ...output.console import exit_ok
from ...output.console import info
from ...output.render import render_result
from ...state import get_state
from ...utils import parse_commalist


state = get_state()

# Create a command group
app = typer.Typer(
    name="cve-allowlist",
    help="Manage the system-wide CVE allowlist.",
    no_args_is_help=True,
)


@app.command("get")
def get_allowlist(ctx: typer.Context) -> None:
    """Get the current CVE allowlist."""
    allowlist = state.run(state.client.get_cve_allowlist(), "Fetching system info...")
    render_result(allowlist, ctx)


@app.command("update")
def update_allowlist(
    ctx: typer.Context,
    cves: List[str] = typer.Option(
        [],
        "--cve",
        help="CVE IDs to add/remove. Can be a comma-separated list, or specified multiple times.",
        callback=parse_commalist,
    ),
    remove: bool = typer.Option(
        False,
        "--remove",
        help="Remove the given CVE IDs from the allowlist instead of adding them.",
    ),
) -> None:
    """Add/remove CVE IDs to the CVE allowlist."""
    current = state.run(state.client.get_cve_allowlist())

    # Check if the current allowlist is defined
    if current.items is None:
        if remove:
            exit_ok("CVE allowlist is empty, nothing to remove.")
        current.items = []

    if remove:
        current.items = [item for item in current.items if item.cve_id not in cves]
    else:
        # Make a list of all CVE IDs in the current allowlist
        current_ids = [item.cve_id for item in current.items if item.cve_id is not None]
        # Create new CVEAllowListItem objects for each CVE ID
        to_add = [
            CVEAllowlistItem(cve_id=cve_id)
            for cve_id in cves
            if cve_id not in current_ids
        ]
        current.items.extend(to_add)

    state.run(state.client.update_cve_allowlist(current), "Updating CVE allowlist...")
    if remove:
        info(
            f"Removed {len(cves)} CVEs from CVE allowlist. Total: {len(current.items)}"
        )
    else:
        info(f"Added {len(cves)} CVEs to CVE allowlist. Total: {len(current.items)}")


@app.command("clear")
def clear_allowlist(
    ctx: typer.Context,
    full_clear: bool = typer.Option(
        False,
        "--full",
        help="Also clear the allowlist of all metadata (such as project ID, expiration, etc).",
    ),
) -> None:
    """Clear the current CVE allowlist of all CVEs, and optionally all metadata as well."""
    if full_clear:
        allowlist = CVEAllowlist(items=[])  # create a whole new allowlist
    else:
        # Fetch existing allowlist to preserve metadata
        allowlist = state.run(
            state.client.get_cve_allowlist(), "Fetching current allowlist..."
        )
        allowlist.items = []

    state.run(state.client.update_cve_allowlist(allowlist), "Clearing CVE allowlist...")
    msg = "Cleared CVE allowlist of CVEs."
    if full_clear:
        msg += " Also cleared metadata."
    info(msg)
