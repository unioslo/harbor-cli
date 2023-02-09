# basically match the auto generated output, except set the panel title
# to "Audit Log Entry", and use a horizontal arrangement rather than the
# vertical arrangement of the auto generated output.
from __future__ import annotations

from typing import Sequence

from harborapi.models.models import AuditLog
from rich.panel import Panel
from rich.table import Table

from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.dates import datetime_str
from ._utils import get_panel
from ._utils import get_table


def auditlog_panel(logs: Sequence[AuditLog]) -> Panel:
    """Renders a list of AuditLog objects as individual tables in a panel."""

    tables = []
    for log in logs:
        tables.append(auditlog_table([log]))
    return get_panel(tables, title="Audit Logs", expand=True)


# Keep arg type as sequnence to match interface, even though it's not used directly
def auditlog_table(logs: Sequence[AuditLog]) -> Table:
    if len(logs) == 1:
        title = None
    else:
        title = "Audit Log Entries"
    table = get_table(
        title,
        logs,
        columns=[
            "ID",
            "Username",
            "Resource",
            "Resource Type",
            "Operation",
            "Time",
        ],
    )
    for log in logs:
        table.add_row(
            int_str(log.id),
            str_str(log.username),
            str_str(log.resource),
            str_str(log.resource_type),
            str_str(log.operation),
            datetime_str(log.op_time),
        )
    return table
