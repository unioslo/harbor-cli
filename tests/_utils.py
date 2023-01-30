from __future__ import annotations

from typing import NamedTuple
from typing import Optional

from pydantic import ValidationError

from harbor_cli.output.table import RENDER_FUNCTIONS


class Parameter(NamedTuple):
    param: str
    value: Optional[str] = None
    ok: bool = True

    @property
    def as_arg(self) -> list[str]:
        if self.value is None:
            return [self.param]
        return [self.param, str(self.value)]


compact_renderables = []
for model in RENDER_FUNCTIONS.keys():
    try:
        obj = model()
    except ValidationError:
        continue
    compact_renderables.append(model)
