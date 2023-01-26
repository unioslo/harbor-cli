from __future__ import annotations

from typing import NamedTuple


class Parameter(NamedTuple):
    param: str
    value: str | None = None
    ok: bool = True

    @property
    def as_arg(self) -> list[str]:
        if self.value is None:
            return [self.param]
        return [self.param, str(self.value)]
