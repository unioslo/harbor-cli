from __future__ import annotations

from pydantic import ByteSize

from .constants import NONE_STR


def bytesize_str(b: int | None, decimal: bool = False) -> str:
    return ByteSize(b).human_readable(decimal=decimal) if b is not None else NONE_STR
