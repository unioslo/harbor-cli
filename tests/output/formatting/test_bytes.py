from __future__ import annotations

import pytest

from harbor_cli.output.formatting.bytes import bytesize_str
from harbor_cli.output.formatting.constants import NONE_STR


@pytest.mark.parametrize(
    "b, expected",
    [
        (-1, NONE_STR),
        (None, NONE_STR),
        (0, "0B"),
        (1, "1B"),
        (1000, "1.0KB"),
        (1023, "1.0KB"),
        (1024, "1.0KB"),
        (1000 * 1000, "1.0MB"),
        (1000 * 1000 * 1000, "1.0GB"),
        (1000 * 1000 * 1000 * 1000, "1.0TB"),
        (1000 * 1000 * 1000 * 1000 * 1000, "1.0PB"),
        (1000 * 1000 * 1000 * 1000 * 1000 * 1000, "1.0EB"),
        (500000000000, "500.0GB"),
    ],
)
def test_bytesize_str_decimal(b: int | None, expected: str) -> None:
    """Test bytesize_str in decimal auto mode."""
    assert bytesize_str(b, decimal=True) == expected


@pytest.mark.parametrize(
    "b, expected",
    [
        (-1, NONE_STR),
        (None, NONE_STR),
        (0, "0B"),
        (1, "1B"),
        (1023, "1023B"),
        (1024, "1.0KiB"),
        (1024 * 1024, "1.0MiB"),
        (1024 * 1024 * 1024, "1.0GiB"),
        (1024 * 1024 * 1024 * 1024, "1.0TiB"),
        (1024 * 1024 * 1024 * 1024 * 1024, "1.0PiB"),
        (1024 * 1024 * 1024 * 1024 * 1024 * 1024, "1.0EiB"),
        (500000000000, "465.7GiB"),
    ],
)
def test_bytesize_str_binary(b: int, expected: str) -> None:
    """Test bytesize_str in binary auto mode."""
    assert bytesize_str(b, decimal=False) == expected
