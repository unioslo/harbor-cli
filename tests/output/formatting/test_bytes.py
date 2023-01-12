from __future__ import annotations

import math

import pytest

from harbor_cli.output.formatting.bytes import ByteFormat
from harbor_cli.output.formatting.bytes import bytes_to_gibibytes
from harbor_cli.output.formatting.bytes import bytes_to_gigabytes
from harbor_cli.output.formatting.bytes import bytes_to_kibibytes
from harbor_cli.output.formatting.bytes import bytes_to_kilobytes
from harbor_cli.output.formatting.bytes import bytes_to_mebibytes
from harbor_cli.output.formatting.bytes import bytes_to_megabytes
from harbor_cli.output.formatting.bytes import bytes_to_str
from harbor_cli.output.formatting.bytes import bytes_to_tebibytes
from harbor_cli.output.formatting.bytes import bytes_to_terabytes


@pytest.mark.parametrize(
    "b, expected",
    [
        (0, "0 B"),
        (1, "1 B"),
        (1000, "1.00 kB"),
        (1023, "1.02 kB"),
        (1024, "1.02 kB"),
        (1000 * 1000, "1.00 MB"),
        (1000 * 1000 * 1000, "1.00 GB"),
        (1000 * 1000 * 1000 * 1000, "1.00 TB"),
        (1000 * 1000 * 1000 * 1000 * 1000, "1000.00 TB"),
        (500000000000, "500.00 GB"),
    ],
)
def test_bytes_to_str_auto(b: int, expected: str) -> None:
    """Test bytes_to_str in decimal auto mode."""
    assert bytes_to_str(b, ByteFormat.AUTO) == expected


@pytest.mark.parametrize(
    "b, expected",
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1.00 KiB"),
        (1024 * 1024, "1.00 MiB"),
        (1024 * 1024 * 1024, "1.00 GiB"),
        (1024 * 1024 * 1024 * 1024, "1.00 TiB"),
        (1024 * 1024 * 1024 * 1024 * 1024, "1024.00 TiB"),
        (500000000000, "465.66 GiB"),
    ],
)
def test_bytes_to_str_auto_binary(b: int, expected: str) -> None:
    """Test bytes_to_str in binary auto mode."""
    assert bytes_to_str(b, ByteFormat.AUTO_BINARY) == expected


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 0.001),
        (1000, 1.0),
        (1024, 1.024),
        (1000 * 1000, 1000.0),
        (1000 * 1000 * 1000, 1000000.0),
        (500000000000, 500000000.0),
    ],
)
def test_bytes_to_kilobytes(b: int, expected: float) -> None:
    res = bytes_to_kilobytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 1e-06),
        (1000, 0.001),
        (1024, 0.001024),
        (1000 * 1000, 1.0),
        (1000 * 1000 * 1000, 1000.0),
        (1000 * 1000 * 1000 * 1000, 1000000.0),
    ],
)
def test_bytes_to_megabytes(b: int, expected: float) -> None:
    res = bytes_to_megabytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 1e-09),
        (1000, 1e-06),
        (1024, 1.024e-06),
        (1000 * 1000, 0.001),
        (1000 * 1000 * 1000, 1.0),
        (1000 * 1000 * 1000 * 1000, 1000.0),
        (500000000000, 500),
    ],
)
def test_bytes_to_gigabytes(b: int, expected: float) -> None:
    res = bytes_to_gigabytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 1e-12),
        (1000, 1e-09),
        (1024, 1.024e-09),
        (1000 * 1000, 1e-06),
        (1000 * 1000 * 1000, 0.001),
        (1000 * 1000 * 1000 * 1000, 1.0),
        (500000000000, 0.5),
    ],
)
def test_bytes_to_terabytes(b: int, expected: float) -> None:
    res = bytes_to_terabytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 0.0009765625),
        (1023, 0.9990234375),
        (1024, 1.0),
        (1024 * 1024, 1024.0),
        (1024 * 1024 * 1024, 1048576.0),
        (500000000000, 488281250.0),
    ],
)
def test_bytes_to_kibibytes(b: int, expected: float) -> None:
    res = bytes_to_kibibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 9.5367431640625e-07),
        (1023, 0.0009756088256835938),
        (1024, 0.0009765625),
        (1024 * 1024, 1.0),
        (1024 * 1024 * 1024, 1024.0),
        (1024 * 1024 * 1024 * 1024, 1048576.0),
    ],
)
def test_bytes_to_mebibytes(b: int, expected: float) -> None:
    res = bytes_to_mebibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 9.313225746154785e-10),
        (1023, 9.527429938316345e-07),
        (1024, 9.5367431640625e-07),
        (1024 * 1024, 0.0009765625),
        (1024 * 1024 * 1024, 1.0),
        (1024 * 1024 * 1024 * 1024, 1024.0),
        (500000000000, 465.66128730773926),
    ],
)
def test_bytes_to_gibibytes(b: int, expected: float) -> None:
    res = bytes_to_gibibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 9.094947017729282e-13),
        (1023, 9.304130799137056e-10),
        (1024, 9.313225746154785e-10),
        (1024 * 1024, 9.5367431640625e-07),
        (1024 * 1024 * 1024, 0.0009765625),
        (1024 * 1024 * 1024 * 1024, 1.0),
        (500000000000, 0.4547473508864641),
    ],
)
def test_bytes_to_tebibytes(b: int, expected: float) -> None:
    res = bytes_to_tebibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)
