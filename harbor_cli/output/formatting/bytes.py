from __future__ import annotations

from pydantic import ByteSize


def bytesize_str(b: int | None, decimal: bool = False) -> str:
    return ByteSize(b or 0).human_readable(decimal=decimal)
