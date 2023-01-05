from __future__ import annotations

from typing import List

import typer
from harborapi.models.models import CVEAllowlist
from harborapi.models.models import CVEAllowlistItem

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import parse_commalist

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
        help="CVE to add to the allowlist. Can be a comma-separated list, or specified multiple times.",
        callback=parse_commalist,
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        help="Replace the existing list with new CVEs. Otherwise, add to the existing list.",
    ),
) -> None:
    """Add CVE IDs to the CVE allowlist."""
    current_list = state.run(state.client.get_cve_allowlist())

    cve_items = [CVEAllowlistItem(cve_id=cve_id) for cve_id in cves]
    if replace:
        current_list.items = cve_items
    else:
        # TODO: deduplicate CVEs
        if current_list.items is None:
            current_list.items = []
        current_list.items += cve_items

    state.run(
        state.client.update_cve_allowlist(current_list), "Updating CVE allowlist..."
    )
    if replace:
        logger.info(f"Replaced CVE allowlist with {len(cves)} CVEs.")
    else:
        logger.info(
            f"Added {len(cves)} CVEs to CVE allowlist. Total: {len(current_list.items)}"
        )


@app.command("clear")
def clear_allowlist(
    ctx: typer.Context,
    full: bool = typer.Option(
        False,
        "--full",
        help="Also clear the allowlist of all metadata (such as project ID, expiration, etc).",
    ),
) -> None:
    """Clear the current CVE allowlist of all CVEs, and optionally all metadata as well."""
    if not full:
        current_list = state.run(
            state.client.get_cve_allowlist(), "Fetching current allowlist..."
        )
        current_list.items = []
        state.run(
            state.client.update_cve_allowlist(current_list),
            "Clearing CVEs from allowlist...",
        )
        logger.info("Cleared CVE allowlist of CVEs.")
    else:
        new_list = CVEAllowlist(items=[])
        state.run(
            state.client.update_cve_allowlist(new_list), "Clearing CVE allowlist..."
        )
        logger.info("Cleared CVE allowlist of CVEs and metadata.")
