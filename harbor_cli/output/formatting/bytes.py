from __future__ import annotations

from enum import Enum
from typing import Final


class ByteFormat(Enum):
    B = "B"
    # Decimal
    KB = "KB"
    MB = "MB"
    GB = "GB"
    TB = "TB"
    # Binary
    KIB = "KIB"
    MIB = "MIB"
    GIB = "GIB"
    TIB = "TIB"
    # Auto (decimal)
    AUTO = "AUTO"
    # Auto (binary)
    AUTO_BINARY = "AUTO_BINARY"


KILOBYTE: Final[int] = 1000
MEGABYTE: Final[int] = 1000**2
GIGABYTE: Final[int] = 1000**3
TERABYTE: Final[int] = 1000**4

KIBIBYTE: Final[int] = 1024
MEBIBYTE: Final[int] = 1024**2
GIBIBYTE: Final[int] = 1024**3
TEBIBYTE: Final[int] = 1024**4


def bytes_to_str(b: int, fmt: ByteFormat = ByteFormat.AUTO) -> str:
    """Create a string representation of a number of bytes.

    Examples
    --------
    >>> bytes_to_str(0)
    '0 B'
    >>> bytes_to_str(1000)
    '1.00 kB'
    >>> bytes_to_str(1024, ByteFormat.AUTO_BINARY)
    '1.00 KiB'

    Parameters
    ----------
    b : int
        The number of bytes.
    fmt : ByteFormat, optional
        The format to use, by default ByteFormat.AUTO.
        AUTO will use decimal units, AUTO_BINARY will use binary units.
        Otherwise, a specific unit can be used.

    Returns
    -------
    str
        The formatted string.

    See Also
    --------
    ByteFormat : The available formats.
    """
    if isinstance(fmt, str):
        fmt = fmt.upper()  # type: ignore # cast to enum line below
    fmt = ByteFormat(fmt)

    # Decimal
    if fmt == ByteFormat.TB:
        return f"{bytes_to_terabytes(b):.2f} TB"
    if fmt == ByteFormat.GB:
        return f"{bytes_to_gigabytes(b):.2f} GB"
    if fmt == ByteFormat.MB:
        return f"{bytes_to_megabytes(b):.2f} MB"
    if fmt == ByteFormat.KB:
        return f"{bytes_to_kilobytes(b):.2f} kB"
    if fmt == ByteFormat.AUTO:
        if b >= TERABYTE:
            return bytes_to_str(b, ByteFormat.TB)
        if b >= GIGABYTE:
            return bytes_to_str(b, ByteFormat.GB)
        if b >= MEGABYTE:
            return bytes_to_str(b, ByteFormat.MB)
        if b >= KILOBYTE:
            return bytes_to_str(b, ByteFormat.KB)
        return bytes_to_str(b, ByteFormat.B)

    # Binary
    if fmt == ByteFormat.TIB:
        return f"{bytes_to_tebibytes(b):.2f} TiB"
    if fmt == ByteFormat.GIB:
        return f"{bytes_to_gibibytes(b):.2f} GiB"
    if fmt == ByteFormat.MIB:
        return f"{bytes_to_mebibytes(b):.2f} MiB"
    if fmt == ByteFormat.KIB:
        return f"{bytes_to_kibibytes(b):.2f} KiB"
    if fmt == ByteFormat.B:
        return f"{b} B"
    if fmt == ByteFormat.AUTO_BINARY:
        if b >= TEBIBYTE:
            return bytes_to_str(b, ByteFormat.TIB)
        if b >= GIBIBYTE:
            return bytes_to_str(b, ByteFormat.GIB)
        if b >= MEBIBYTE:
            return bytes_to_str(b, ByteFormat.MIB)
        if b >= KIBIBYTE:
            return bytes_to_str(b, ByteFormat.KIB)
        return bytes_to_str(b, ByteFormat.B)

    raise ValueError(f"Unknown byte format: {fmt}")


def bytes_to_terabytes(b: int) -> float:
    """Convert bytes to terabytes."""
    return b / TERABYTE


def bytes_to_gigabytes(b: int) -> float:
    """Convert bytes to gigabytes."""
    return b / GIGABYTE


def bytes_to_megabytes(b: int) -> float:
    """Convert bytes to megabytes."""
    return b / MEGABYTE


def bytes_to_kilobytes(b: int) -> float:
    """Convert bytes to kilobytes."""
    return b / KILOBYTE


def bytes_to_tebibytes(b: int) -> float:
    """Convert bytes to tebibytes."""
    return b / TEBIBYTE


def bytes_to_gibibytes(b: int) -> float:
    """Convert bytes to gibibytes."""
    return b / GIBIBYTE


def bytes_to_mebibytes(b: int) -> float:
    """Convert bytes to mebibytes."""
    return b / MEBIBYTE


def bytes_to_kibibytes(b: int) -> float:
    """Convert bytes to kibibytes."""
    return b / KIBIBYTE
