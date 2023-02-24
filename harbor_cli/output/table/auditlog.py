# basically match the auto generated output, except set the panel title
# to "Audit Log Entry", and use a horizontal arrangement rather than the
# vertical arrangement of the auto generated output.
from __future__ import annotations

from typing import Any
from typing import Sequence

from harborapi.models.models import AuditLog
from rich.table import Table

from ..formatting.builtin import int_str
from ..formatting.builtin import str_str
from ..formatting.dates import datetime_str
from ._utils import get_table


def auditlog_table(logs: Sequence[AuditLog], **kwargs: Any) -> Table:
    table = get_table(
        "Audit Log",
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
