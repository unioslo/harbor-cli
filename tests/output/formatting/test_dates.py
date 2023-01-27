from __future__ import annotations

from datetime import datetime

import pytest

from harbor_cli.output.formatting.dates import datetime_str


@pytest.mark.parametrize(
    "inp,with_time,subsecond,expected",
    [
        (datetime(2020, 1, 1), True, False, "2020-01-01 00:00:00"),
        (datetime(2020, 1, 1), True, True, "2020-01-01 00:00:00.000000"),
        (datetime(2020, 1, 1), False, True, "2020-01-01"),
        (datetime(2020, 1, 1), False, False, "2020-01-01"),
    ],
)
def test_datetime_str(
    inp: datetime, subsecond: bool, with_time: bool, expected: str
) -> None:
    assert datetime_str(inp, with_time=with_time, subsecond=subsecond) == expected
