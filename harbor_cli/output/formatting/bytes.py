from __future__ import annotations

from pydantic import ByteSize


def bytesize_str(b: int, decimal: bool = False) -> str:
    return ByteSize(b).human_readable(decimal=decimal)


def bytesize_to_exabytes(b: int) -> float:
    """Convert bytes to exabytes."""
    return ByteSize(b).to("EB")


def bytesize_to_petabytes(b: int) -> float:
    """Convert bytes to petabytes."""
    return ByteSize(b).to("PB")


def bytesize_to_terabytes(b: int) -> float:
    """Convert bytes to terabytes."""
    return ByteSize(b).to("TB")


def bytesize_to_gigabytes(b: int) -> float:
    """Convert bytes to gigabytes."""
    return ByteSize(b).to("GB")


def bytesize_to_megabytes(b: int) -> float:
    """Convert bytes to megabytes."""
    return ByteSize(b).to("MB")


def bytesize_to_kilobytes(b: int) -> float:
    """Convert bytes to kilobytes."""
    return ByteSize(b).to("KB")


def bytesize_to_exbibytes(b: int) -> float:
    """Convert bytes to exbibytes."""
    return ByteSize(b).to("EiB")


def bytesize_to_pebibytes(b: int) -> float:
    """Convert bytes to pebibytes."""
    return ByteSize(b).to("PiB")


def bytesize_to_tebibytes(b: int) -> float:
    """Convert bytes to tebibytes."""
    return ByteSize(b).to("TiB")


def bytesize_to_gibibytes(b: int) -> float:
    """Convert bytes to gibibytes."""
    return ByteSize(b).to("GiB")


def bytesize_to_mebibytes(b: int) -> float:
    """Convert bytes to mebibytes."""
    return ByteSize(b).to("MiB")


def bytesize_to_kibibytes(b: int) -> float:
    """Convert bytes to kibibytes."""
    return ByteSize(b).to("KiB")
