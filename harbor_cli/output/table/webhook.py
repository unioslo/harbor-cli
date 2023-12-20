from __future__ import annotations

from itertools import zip_longest
from typing import Any
from typing import Sequence

from harborapi.models.models import SupportedWebhookEventTypes
from rich.table import Table

from ..formatting.builtin import str_str
from ._utils import get_table


def supported_events_table(
    supported_events: Sequence[SupportedWebhookEventTypes], **kwargs: Any
) -> Table:
    """Display one or more repositories in a table."""
    table = get_table(
        "Supported Webhook Events",
        columns=[
            "Event Types",
            "Notify Types",
        ],
    )
    for events in supported_events:
        ev = events.event_type or []
        nt = events.notify_type or []
        for event, notify in zip_longest(ev, nt, fillvalue=None):
            table.add_row(
                str_str(event.root if event else ""),
                str_str(notify.root if notify else ""),
            )
    return table
