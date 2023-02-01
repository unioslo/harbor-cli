from __future__ import annotations

from pydantic import ByteSize


def bytesize_str(b: int, decimal: bool = False) -> str:
    return ByteSize(b).human_readable(decimal=decimal)
