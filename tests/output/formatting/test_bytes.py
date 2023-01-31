from __future__ import annotations

import math

import pytest

from harbor_cli.output.formatting.bytes import bytesize_str
from harbor_cli.output.formatting.bytes import bytesize_to_exabytes
from harbor_cli.output.formatting.bytes import bytesize_to_exbibytes
from harbor_cli.output.formatting.bytes import bytesize_to_gibibytes
from harbor_cli.output.formatting.bytes import bytesize_to_gigabytes
from harbor_cli.output.formatting.bytes import bytesize_to_kibibytes
from harbor_cli.output.formatting.bytes import bytesize_to_kilobytes
from harbor_cli.output.formatting.bytes import bytesize_to_mebibytes
from harbor_cli.output.formatting.bytes import bytesize_to_megabytes
from harbor_cli.output.formatting.bytes import bytesize_to_pebibytes
from harbor_cli.output.formatting.bytes import bytesize_to_petabytes
from harbor_cli.output.formatting.bytes import bytesize_to_tebibytes
from harbor_cli.output.formatting.bytes import bytesize_to_terabytes


@pytest.mark.parametrize(
    "b, expected",
    [
        (0, "0.0B"),
        (1, "1.0B"),
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
def test_bytesize_str_decimal(b: int, expected: str) -> None:
    """Test bytesize_str in decimal auto mode."""
    assert bytesize_str(b, decimal=True) == expected


@pytest.mark.parametrize(
    "b, expected",
    [
        (0, "0.0B"),
        (1, "1.0B"),
        (1023, "1023.0B"),
        (1024, "1.0KiB"),
        (1024 * 1024, "1.0MiB"),
        (1024 * 1024 * 1024, "1.0GiB"),
        (1024 * 1024 * 1024 * 1024, "1.0TiB"),
        (1024 * 1024 * 1024 * 1024 * 1024, "1.0PiB"),
        (1024 * 1024 * 1024 * 1024 * 1024 * 1024, "1.0EiB"),
        (500000000000, "465.7GiB"),
    ],
)
def test_bytesize_str_auto_binary(b: int, expected: str) -> None:
    """Test bytesize_str in binary auto mode."""
    assert bytesize_str(b, decimal=False) == expected


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
def test_bytesize_to_kilobytes(b: int, expected: float) -> None:
    res = bytesize_to_kilobytes(b)
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
def test_bytesize_to_megabytes(b: int, expected: float) -> None:
    res = bytesize_to_megabytes(b)
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
def test_bytesize_to_gigabytes(b: int, expected: float) -> None:
    res = bytesize_to_gigabytes(b)
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
def test_bytesize_to_terabytes(b: int, expected: float) -> None:
    res = bytesize_to_terabytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 1e-15),
        (1000, 1e-12),
        (1024, 1.024e-12),
        (1000 * 1000, 1e-09),
        (1000 * 1000 * 1000, 1e-06),
        (1000 * 1000 * 1000 * 1000, 0.001),
        (1000 * 1000 * 1000 * 1000 * 1000, 1.0),
        (500000000000, 0.0005),
    ],
)
def test_bytesize_to_petabytes(b: int, expected: float) -> None:
    res = bytesize_to_petabytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 1e-18),
        (1000, 1e-15),
        (1024, 1.024e-15),
        (1000 * 1000, 1e-12),
        (1000 * 1000 * 1000, 1e-09),
        (1000 * 1000 * 1000 * 1000, 1e-06),
        (1000 * 1000 * 1000 * 1000 * 1000, 0.001),
        (1000 * 1000 * 1000 * 1000 * 1000 * 1000, 1.0),
        (500000000000, 5e-07),
    ],
)
def test_bytesize_to_exabytes(b: int, expected: float) -> None:
    res = bytesize_to_exabytes(b)
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
def test_bytesize_to_kibibytes(b: int, expected: float) -> None:
    res = bytesize_to_kibibytes(b)
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
def test_bytesize_to_mebibytes(b: int, expected: float) -> None:
    res = bytesize_to_mebibytes(b)
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
def test_bytesize_to_gibibytes(b: int, expected: float) -> None:
    res = bytesize_to_gibibytes(b)
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
def test_bytesize_to_tebibytes(b: int, expected: float) -> None:
    res = bytesize_to_tebibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 8.881784197001252e-16),
        (1023, 9.086065233532281e-13),
        (1024, 9.094947017729282e-13),
        (1024 * 1024, 9.313225746154785e-10),
        (1024 * 1024 * 1024, 9.5367431640625e-07),
        (1024 * 1024 * 1024 * 1024, 0.0009765625),
        (1024 * 1024 * 1024 * 1024 * 1024, 1.0),
        (500000000000, 0.0004440892098500626),
    ],
)
def test_bytesize_to_pebibytes(b: int, expected: float) -> None:
    res = bytesize_to_pebibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)


@pytest.mark.parametrize(
    "b,expected",
    [
        (0, 0.0),
        (1, 8.673617379884035e-19),
        (1023, 8.873110579621368e-16),
        (1024, 8.881784197001252e-16),
        (1024 * 1024, 9.094947017729282e-13),
        (1024 * 1024 * 1024, 9.313225746154785e-10),
        (1024 * 1024 * 1024 * 1024, 9.5367431640625e-07),
        (1024 * 1024 * 1024 * 1024 * 1024, 0.0009765625),
        (1024 * 1024 * 1024 * 1024 * 1024 * 1024, 1.0),
        (500000000000, 4.336808689942018e-07),
    ],
)
def test_bytesize_to_exbibytes(b: int, expected: float) -> None:
    res = bytesize_to_exbibytes(b)
    assert math.isclose(res, expected, rel_tol=0.01)
